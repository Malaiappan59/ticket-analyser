# ─────────────────────────────────────────────────────────────────────────────
# app.py  –  IT Ticket Volume Dump Analyser
# Run with:  streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Path bootstrap (works whether run from root or subdirectory) ─────────────
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import CATEGORIES, CATEGORY_COLORS, APP_NAME, APP_VERSION
from core.classifier import check_ollama_available, classify_batch, get_available_models
from core.exporter import create_output_excel
from core.preprocessor import (
    apply_filters,
    clean_dataframe,
    detect_columns,
    get_filter_options,
    load_file,
    validate_dataframe,
)
from utils.helpers import format_duration, generate_sample_data

# ─────────────────────────────────────────────────────────────────────────────
# Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ITSM Ticket Analyser",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": f"{APP_NAME} v{APP_VERSION}"},
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

/* ── Theme tokens ───────────────────────────────────────────────────── */
:root {
    --bg-main: #0B1020;
    --bg-panel: #121A2B;
    --bg-panel-2: #182338;
    --bg-soft: #1E293B;
    --text-main: #F8FAFC;
    --text-muted: #CBD5E1;
    --border: #24324A;
    --accent: #1976D2;
    --accent-2: #42A5F5;
    --success-bg: #DCFCE7;
    --success-text: #166534;
    --error-bg: #FEE2E2;
    --error-text: #991B1B;
    --warn-bg: #FEF3C7;
    --warn-text: #92400E;
}

/* ── Base ───────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Sans', sans-serif;
    background: var(--bg-main);
    color: var(--text-main);
}

/* Main app area */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background: var(--bg-main) !important;
}

/* Main content block */
.main .block-container {
    background: transparent !important;
    color: var(--text-main) !important;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Generic text fixes */
h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: var(--text-main);
}

small, .stCaption, .stMarkdown p {
    color: var(--text-muted) !important;
}

/* Streamlit widgets */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stNumberInput input,
.stFileUploader,
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background: var(--bg-panel) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* Expanders / containers */
details, .stExpander, [data-testid="stExpander"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-main) !important;
}

/* Dataframe / table containers */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background: var(--bg-panel) !important;
    border-radius: 12px !important;
}

/* ── Header banner ──────────────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #0D47A1 0%, #1565C0 55%, #1976D2 100%);
    border-radius: 14px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.4rem;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    box-shadow: 0 4px 24px rgba(13,71,161,0.25);
}
.app-header .icon { font-size: 2.6rem; }
.app-header h1 { margin:0; font-size:1.55rem; font-weight:700; letter-spacing:-0.02em; color:#fff; }
.app-header p  { margin:0.2rem 0 0; font-size:0.88rem; opacity:0.92; color:#EAF2FF; }
.badge {
    background: rgba(255,255,255,0.16);
    border-radius: 20px;
    padding: 0.15rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
    margin-top: 0.4rem;
    color: #fff;
}

/* ── Metric cards ───────────────────────────────────────────────────── */
.metric-row { display:flex; gap:1rem; margin-bottom:1.2rem; }
.metric-card {
    flex:1;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.22);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #6CB6FF;
    font-family:'IBM Plex Mono', monospace;
}
.metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 0.2rem;
}
.metric-delta { font-size:0.8rem; color:#4ADE80; font-weight:600; }

/* ── Status pills ───────────────────────────────────────────────────── */
.pill-ok  {
    background: var(--success-bg);
    color: var(--success-text);
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.82rem;
    font-weight: 600;
}
.pill-err {
    background: var(--error-bg);
    color: var(--error-text);
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.82rem;
    font-weight: 600;
}
.pill-warn {
    background: var(--warn-bg);
    color: var(--warn-text);
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.82rem;
    font-weight: 600;
}

/* ── Ollama status box ──────────────────────────────────────────────── */

/*
.ollama-ok {
    background:#123524;
    border:1px solid #1F7A4D;
    border-radius:8px;
    padding:0.6rem 0.9rem;
    color:#BBF7D0;
    font-size:0.85rem;
}
*/

.ollama-ok {
    background:#DCFCE7; border:1px solid #86EFAC;
    border-radius:8px; padding:0.6rem 0.9rem;
    color:#14532D; font-size:0.85rem;
}

.ollama-err {
    background:#3A1616;
    border:1px solid #B91C1C;
    border-radius:8px;
    padding:0.6rem 0.9rem;
    color:#FECACA;
    font-size:0.85rem;
}

/* ── Section titles ─────────────────────────────────────────────────── */
.section-title {
    font-size:1.05rem;
    font-weight:700;
    color:#60A5FA;
    border-left:4px solid #42A5F5;
    padding-left:0.7rem;
    margin:1rem 0 0.6rem;
}

/* ── Info box ───────────────────────────────────────────────────────── */
.info-box {
    background: #10233E;
    border: 1px solid #24476F;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.88rem;
    color: #D9EAFE;
}

/* ── Hide Streamlit chrome ──────────────────────────────────────────── */
#MainMenu, footer, header { visibility:hidden; }
.stDeployButton { display:none; }

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    padding: 0.55rem 1.1rem;
    border-radius: 8px 8px 0 0;
    color: var(--text-muted) !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #FF6B6B !important;
    border-bottom: 3px solid #FF6B6B !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(135deg,#0D47A1,#1976D2) !important;
    color:#fff !important;
    border:none !important;
    border-radius:8px !important;
    font-weight:600 !important;
    padding:0.6rem 1rem !important;
}
.stDownloadButton > button {
    width:100% !important;
}

/* ── Progress bar ───────────────────────────────────────────────────── */
.stProgress > div > div {
    background:#1976D2;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #E9EEF8 !important;
    border-right: 1px solid #D7E0F0;
}
[data-testid="stSidebar"] * {
    color: #0F172A !important;
}

/* Sidebar cards / inner blocks if needed */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stFileUploader,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1px solid #D7E0F0 !important;
    color: #0F172A !important;
}

/* ── Optional card wrapper for custom markdown blocks ──────────────── */
.panel-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "df":                None,
    "classified_df":     None,
    "col_mappings":      {},
    "col_mappings_user": {},
    "file_name":         None,
    "analysis_done":     False,
    "ollama_ok":         False,
    "ollama_msg":        "",
    "available_models":  [],
    "selected_model":    "llama3.2",
    "use_llm":           True,
    "output_excel":      None,
    "sample_csv":        None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# Helper: check Ollama (cached per session)
# ─────────────────────────────────────────────────────────────────────────────
def refresh_ollama_status() -> None:
    ok, msg = check_ollama_available()
    st.session_state.ollama_ok  = ok
    st.session_state.ollama_msg = msg
    if ok:
        st.session_state.available_models = get_available_models()


if not st.session_state.ollama_msg:
    refresh_ollama_status()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
    <div style="text-align:center;padding:1.2rem 0 0.5rem;">
        <div style="font-size:2.8rem;">🎫</div>
        <div style="font-weight:700;font-size:1.1rem;color:#0D47A1;margin-top:0.3rem;">
            ITSM Ticket Analyser
        </div>
        <div style="font-size:0.72rem;color:#6B7280;margin-top:0.1rem;">
            AI-Powered ITSM Classification
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Ollama status ────────────────────────────────────────────────────────
    top_c, btn_c = st.columns([4, 1])
    with top_c:
        st.markdown("**🤖 Ollama Status**")
    with btn_c:
        if st.button("↺", help="Refresh Ollama status", key="refresh_btn"):
            refresh_ollama_status()

    if st.session_state.ollama_ok:
        n_models = len(st.session_state.available_models)
        st.markdown(
            f'<div class="ollama-ok">✅ <strong>Running</strong>'
            f"<br><small>{n_models} model(s) available</small></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="ollama-err">❌ <strong>Not running</strong>'
            "<br><small>Keyword mode will be used</small></div>",
            unsafe_allow_html=True,
        )
        with st.expander("▶ How to start Ollama"):
            st.code("# 1. Install Ollama\ncurl https://ollama.ai/install.sh | sh")
            st.code("# 2. Start server\nollama serve")
            st.code("# 3. Pull a model\nollama pull llama3.2")

    st.markdown("")

    # ── Processing mode ──────────────────────────────────────────────────────
    st.markdown("**⚙️ Processing Mode**")
    mode_options = (
        ["🤖 LLM (Ollama)", "🔑 Keyword Only"]
        if st.session_state.ollama_ok
        else ["🔑 Keyword Only (Ollama offline)"]
    )
    selected_mode = st.radio(
        "Mode",
        mode_options,
        label_visibility="collapsed",
        help="LLM = smarter; Keyword = faster & offline",
    )
    st.session_state.use_llm = "LLM" in selected_mode and st.session_state.ollama_ok

    if st.session_state.ollama_ok and st.session_state.use_llm:
        model_list = st.session_state.available_models or ["llama3.2"]
        chosen_model = st.selectbox(
            "Model",
            model_list,
            help="Ollama model used for classification",
        )
        st.session_state.selected_model = chosen_model

    st.divider()

    # ── Categories quick reference ───────────────────────────────────────────
    st.markdown("**📂 12 Categories**")
    cat_list = list(CATEGORIES.keys())
    c1, c2 = st.columns(2)
    for i, cat in enumerate(cat_list):
        color = CATEGORY_COLORS.get(cat, "888888")
        label = f"<span style='background:#{color};color:#111;border-radius:5px;padding:2px 7px;font-size:0.78rem;font-weight:600;'>{cat}</span>"
        (c1 if i % 2 == 0 else c2).markdown(label + "<br>", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        f"<div style='font-size:0.72rem;color:#9CA3AF;text-align:center;'>"
        f"v{APP_VERSION} · Streamlit + Ollama</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
    <div class="icon">🎫</div>
    <div>
        <h1>ITSM Ticket Volume Dump Analyser</h1>
        <p>Automatically classify 10K+ ITSM tickets from ServiceNow/Jira that come from Monitoring and Observability tool like Datadog · Splunk · SolarWinds</p>
        <span class="badge">CPU · Memory · Storage · Network · Hardware · Middleware · Application · Database · Security · OS · Monitoring · Others</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["📤   Upload & Configure", "📊   Results & Export"])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 – Upload & Configure
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    left_col, right_col = st.columns([1, 1], gap="large")

    # ── LEFT: File upload ─────────────────────────────────────────────────────
    with left_col:
        st.markdown('<div class="section-title">📁 Upload Ticket File</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Drag & drop or click to browse",
            type=["csv", "xlsx", "xls"],
            help="Export your ITSM tickets as CSV or Excel and upload here.",
        )

        if uploaded is not None:
            with st.spinner("Reading file…"):
                df, msg = load_file(uploaded)

            if df is not None:
                df = clean_dataframe(df)
                st.session_state.df            = df
                st.session_state.file_name     = uploaded.name
                st.session_state.col_mappings  = detect_columns(df)
                st.session_state.analysis_done = False
                st.session_state.classified_df  = None
                st.session_state.output_excel   = None

                st.success(
                    f"✅ **{uploaded.name}** loaded — "
                    f"**{len(df):,} rows** × **{len(df.columns)} columns**"
                )

                is_ok, issues = validate_dataframe(df)
                for iss in issues:
                    if iss.startswith("❌"):
                        st.error(iss)
                    else:
                        st.warning(iss)

                with st.expander("👁️ Preview first 5 rows"):
                    st.dataframe(df.head(), use_container_width=True, hide_index=True)
            else:
                st.error(f"❌ {msg}")

        else:
            # Show info + sample download
            st.markdown(
                """
<div class="info-box">
    <strong>📋 Expected columns (ServiceNow / Jira format)</strong><br>
    <code>Number, Type, Short_Description, Description,
    Caller_ID, Assignment_Group, Priority, Status, Domain, Work_Notes, Remarks</code><br><br>
    <strong>💡 Tip:</strong> Export your tickets list view as CSV and upload above.
    Any column order is fine – the tool auto-detects columns.
</div>
""",
                unsafe_allow_html=True,
            )

            # Generate sample
            if st.button("🔧 Generate sample 750-ticket CSV", use_container_width=True):
                sample_df = generate_sample_data(750)
                st.session_state.sample_csv = sample_df.to_csv(index=False).encode()

            if st.session_state.sample_csv:
                st.download_button(
                    "⬇️ Download sample_tickets.csv",
                    data=st.session_state.sample_csv,
                    file_name="sample_tickets.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary",
                )

    # ── RIGHT: Column mapping ─────────────────────────────────────────────────
    with right_col:
        if st.session_state.df is not None:
            df      = st.session_state.df
            auto    = st.session_state.col_mappings
            all_c   = ["(Not mapped)"] + list(df.columns)

            st.markdown('<div class="section-title">🗂️ Column Mapping</div>', unsafe_allow_html=True)
            st.caption("Auto-detected – adjust if any column is wrong.")

            def _sel(label: str, field: str, icon: str = "•") -> str:
                default = auto.get(field, "(Not mapped)")
                idx     = all_c.index(default) if default in all_c else 0
                return st.selectbox(f"{icon} {label}", all_c, index=idx, key=f"map_{field}")

            c_id     = _sel("Ticket ID / Number",    "id",               "🔖")
            c_type   = _sel("Ticket Type",            "type",             "📌")
            c_sd     = _sel("Short Description ★",   "short_description","📝")
            c_desc   = _sel("Full Description ★",    "description",      "📄")
            c_status = _sel("Status",                 "status",           "🚦")
            c_group  = _sel("Assignment Group",       "assignment_group", "👥")
            c_caller = _sel("Caller / Requester",     "caller_id",        "👤")

            st.caption("★ At least one description column is required for classification.")

            # Save user overrides
            st.session_state.col_mappings_user = {
                "id":               c_id,
                "type":             c_type,
                "short_description": c_sd,
                "description":      c_desc,
                "status":           c_status,
                "assignment_group": c_group,
                "caller_id":        c_caller,
            }

    # ── Analysis controls ─────────────────────────────────────────────────────
    if st.session_state.df is not None:
        st.divider()
        st.markdown('<div class="section-title">🚀 Run Classification</div>', unsafe_allow_html=True)

        ac1, ac2, ac3 = st.columns([3, 1, 1])

        with ac1:
            mode_label = (
                f"Mode: {'🤖 LLM (Ollama / ' + st.session_state.selected_model + ')' if st.session_state.use_llm else '🔑 Keyword Only'}"
            )
            st.info(
                f"{mode_label}  ·  "
                f"**{len(st.session_state.df):,} tickets** to classify"
            )

        with ac2:
            run_btn = st.button(
                "▶  Start Analysis",
                type="primary",
                use_container_width=True,
                key="run_btn",
            )
        with ac3:
            reset_btn = st.button(
                "🗑  Reset All",
                use_container_width=True,
                key="reset_btn",
            )

        if reset_btn:
            for k, v in _DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

        # ── Run analysis ──────────────────────────────────────────────────────
        if run_btn:
            df      = st.session_state.df
            um      = st.session_state.col_mappings_user
            c_sd    = um.get("short_description")
            c_desc  = um.get("description")
            c_type  = um.get("type")

            # Guard: need at least one text column
            if (not c_sd or c_sd == "(Not mapped)") and (not c_desc or c_desc == "(Not mapped)"):
                st.error("❌ Map at least one description column before running.")
            else:
                c_sd   = None if c_sd   == "(Not mapped)" else c_sd
                c_desc = None if c_desc == "(Not mapped)" else c_desc
                c_type = None if c_type == "(Not mapped)" else c_type

                prog_bar   = st.progress(0.0)
                stat_text  = st.empty()
                stat_text.markdown("**⚙️ Initialising…**")
                t_start    = time.time()

                def _cb(current: int, total: int) -> None:
                    pct     = current / total
                    elapsed = time.time() - t_start
                    rate    = current / elapsed if elapsed else 0
                    eta     = (total - current) / rate if rate else 0
                    prog_bar.progress(pct)
                    stat_text.markdown(
                        f"**⚙️ Classifying…**  {current:,} / {total:,}  ·  "
                        f"{rate:.1f} tickets/s  ·  ETA {format_duration(eta)}"
                    )

                try:
                    cats = classify_batch(
                        tickets_df=df,
                        short_desc_col=c_sd,
                        desc_col=c_desc,
                        type_col=c_type,
                        use_llm=st.session_state.use_llm,
                        model=st.session_state.selected_model,
                        progress_callback=_cb,
                    )

                    prog_bar.progress(1.0)
                    elapsed = time.time() - t_start

                    classified = df.copy()
                    classified.insert(0, "Category", cats)
                    st.session_state.classified_df = classified
                    st.session_state.analysis_done = True

                    with st.spinner("📊 Building Excel output…"):
                        st.session_state.output_excel = create_output_excel(
                            df, classified, "Category"
                        )

                    stat_text.success(
                        f"✅ Done! **{len(df):,} tickets** classified in "
                        f"**{format_duration(elapsed)}** "
                        f"({len(df)/elapsed:.1f} tickets/s)"
                    )
                    st.balloons()
                    st.info("👉 Switch to the **Results & Export** tab to view and download.")

                except Exception as exc:  # noqa: BLE001
                    stat_text.error(f"❌ Classification failed: {exc}")
                    with st.expander("Error details"):
                        st.exception(exc)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 – Results & Export
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.analysis_done or st.session_state.classified_df is None:
        st.markdown(
            """
<div style="text-align:center;padding:4rem 2rem;color:#9CA3AF;">
    <div style="font-size:4rem;">📊</div>
    <h3 style="color:#6B7280;margin:0.5rem 0;">No results yet</h3>
    <p>Upload a ticket file and run analysis in the <strong>Upload &amp; Configure</strong> tab first.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.stop()

    cdf  = st.session_state.classified_df
    um   = st.session_state.col_mappings_user
    total = len(cdf)

    # ── KPI metrics ───────────────────────────────────────────────────────────
    cat_counts  = cdf["Category"].value_counts()
    top_cat     = cat_counts.idxmax() if len(cat_counts) else "N/A"
    top_count   = int(cat_counts.max()) if len(cat_counts) else 0
    others_cnt  = int(cat_counts.get("Others", 0))
    classified  = total - others_cnt
    class_pct   = classified / total * 100 if total else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 Total Tickets",        f"{total:,}")
    m2.metric("✅ Classified",           f"{classified:,}",
              delta=f"{class_pct:.1f}%")
    m3.metric(f"🏆 Top: {top_cat}",      f"{top_count:,} tickets")
    m4.metric("❓ Others (unclassified)", f"{others_cnt:,}",
              delta=f"{-others_cnt/total*100:.1f}%" if others_cnt else "0%",
              delta_color="inverse")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔍 Filter Results</div>', unsafe_allow_html=True)

    c_grp_col    = um.get("assignment_group", "(Not mapped)")
    c_status_col = um.get("status",           "(Not mapped)")
    c_id_col     = um.get("id",               "(Not mapped)")

    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])

    with f1:
        grp_opts = ["All"] + (
            get_filter_options(cdf, c_grp_col) if c_grp_col != "(Not mapped)" else []
        )
        f_group = st.selectbox("👥 Assignment Group", grp_opts, key="f_group")

    with f2:
        status_opts = ["All"] + (
            get_filter_options(cdf, c_status_col) if c_status_col != "(Not mapped)" else []
        )
        f_status = st.selectbox("🚦 Status", status_opts, key="f_status")

    with f3:
        f_id = st.text_input("🔖 Ticket ID Search", placeholder="e.g. INC000…", key="f_id")

    with f4:
        f_cats = st.multiselect(
            "📂 Categories",
            options=list(CATEGORIES.keys()),
            default=list(CATEGORIES.keys()),
            key="f_cats",
        )

    filtered = apply_filters(
        cdf,
        assignment_group=f_group if f_group != "All" else None,
        status=f_status if f_status != "All" else None,
        ticket_id=f_id or None,
        category=f_cats or None,
        assignment_group_col=c_grp_col if c_grp_col != "(Not mapped)" else None,
        status_col=c_status_col if c_status_col != "(Not mapped)" else None,
        id_col=c_id_col if c_id_col != "(Not mapped)" else None,
    )

    st.caption(f"Showing **{len(filtered):,}** of **{total:,}** tickets")

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📈 Distribution</div>', unsafe_allow_html=True)

    chart_data = (
        filtered["Category"].value_counts().reset_index()
    )
    chart_data.columns = ["Category", "Count"]

    color_map = {c: f"#{h}" for c, h in CATEGORY_COLORS.items()}

    ch1, ch2 = st.columns([3, 2])

    with ch1:
        fig_bar = px.bar(
            chart_data,
            x="Category",
            y="Count",
            color="Category",
            color_discrete_map=color_map,
            text="Count",
            title="Ticket Count by Category",
        )
        fig_bar.update_layout(
            showlegend=False,
            height=360,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=10, r=10),
            xaxis=dict(tickangle=-30, tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#EEF2FF"),
        )
        fig_bar.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_bar, use_container_width=True)

    with ch2:
        fig_pie = px.pie(
            chart_data,
            values="Count",
            names="Category",
            color="Category",
            color_discrete_map=color_map,
            hole=0.42,
            title="Category Share",
        )
        fig_pie.update_layout(
            height=360,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=5, l=5, r=5),
            legend=dict(orientation="v", x=1.02, font=dict(size=10)),
        )
        fig_pie.update_traces(textinfo="percent", textfont_size=11)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Category Summary</div>', unsafe_allow_html=True)

    summary_rows = []
    total_f = len(filtered)
    for cat in CATEGORIES:
        cnt = int((filtered["Category"] == cat).sum())
        pct = cnt / total_f * 100 if total_f else 0
        summary_rows.append({
            "Category":   cat,
            "Count":      cnt,
            "Percentage": f"{pct:.1f}%",
            "Share":      "█" * max(0, int(pct / 2)),
        })
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        height=440,
        column_config={
            "Count": st.column_config.NumberColumn("Count", format="%d"),
            "Share": st.column_config.TextColumn("Visual Share", width="medium"),
        },
    )

    st.divider()

    # ── Full ticket table ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 Ticket Table</div>', unsafe_allow_html=True)

    show_all = st.toggle("Show all columns", value=False)
    if show_all:
        display_df = filtered
    else:
        key_fields = ["id", "type", "short_description", "status", "assignment_group"]
        keep = ["Category"]
        for field in key_fields:
            col = um.get(field)
            if col and col != "(Not mapped)" and col in filtered.columns:
                keep.append(col)
        missing = [c for c in keep if c not in filtered.columns]
        if missing:
            display_df = filtered
        else:
            display_df = filtered[keep]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">💾 Export</div>', unsafe_allow_html=True)
    exp1, exp2, exp3 = st.columns(3)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

    with exp1:
        if st.session_state.output_excel:
            st.download_button(
                label="📥 Download Classified Excel",
                data=st.session_state.output_excel,
                file_name=f"classified_tickets_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )
            st.caption(
                "3 sheets: **Classified Tickets** | **All Tickets** | **Category Summary**"
            )

    with exp2:
        csv_bytes = filtered.to_csv(index=False).encode()
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv_bytes,
            file_name=f"filtered_tickets_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Current filtered view as plain CSV")

    with exp3:
        # Regenerate Excel from current filtered view
        if st.button("🔄 Regenerate Excel (filtered view)", use_container_width=True):
            with st.spinner("Building Excel…"):
                regen = create_output_excel(
                    st.session_state.df, filtered, "Category"
                )
            st.download_button(
                label="📥 Download Filtered Excel",
                data=regen,
                file_name=f"filtered_classified_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        st.caption("Excel based on filtered results only")
