# ─────────────────────────────────────────────────────────────────────────────
# core/preprocessor.py  –  File loading, column detection, cleaning, filtering
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import io
import logging
from typing import Optional

import pandas as pd

from config.settings import COLUMN_MAPPINGS, STATUS_NORMALISE

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# File loading
# ─────────────────────────────────────────────────────────────────────────────

def load_file(uploaded_file) -> tuple[Optional[pd.DataFrame], str]:
    """
    Load an uploaded Streamlit file object into a DataFrame.

    Supports: .csv, .xlsx, .xls

    Returns
    -------
    (DataFrame, success_message)  on success
    (None, error_message)         on failure
    """
    try:
        name = uploaded_file.name.lower()
        raw_bytes = uploaded_file.read()

        if name.endswith(".csv"):
            # Try common encodings
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return None, "Could not decode CSV – try saving as UTF-8."
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw_bytes))
        else:
            return None, "Unsupported file type.  Please upload .csv, .xlsx, or .xls"

        if df.empty:
            return None, "The uploaded file contains no data rows."

        # Normalise column names: lowercase + underscores
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
            .str.replace(r"[^\w]", "_", regex=True)
        )
        # Remove duplicate column suffixes added by pandas (_1, _2 …)
        seen: dict[str, int] = {}
        new_cols = []
        for col in df.columns:
            base = col.rstrip("_0123456789")
            if base in seen:
                seen[base] += 1
                new_cols.append(f"{base}_{seen[base]}")
            else:
                seen[base] = 0
                new_cols.append(col)
        df.columns = new_cols

        return df, f"Loaded {len(df):,} rows × {len(df.columns)} columns"

    except Exception as exc:  # noqa: BLE001
        logger.exception("load_file error")
        return None, f"Error loading file: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Column auto-detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_columns(df: pd.DataFrame) -> dict[str, str]:
    """
    Try to automatically map logical field names → actual column names in *df*.
    Returns a dict like: {"id": "number", "status": "state", ...}
    """
    detected: dict[str, str] = {}
    df_col_set = set(df.columns.tolist())

    for field, candidates in COLUMN_MAPPINGS.items():
        for candidate in candidates:
            normalised = candidate.strip().lower().replace(" ", "_")
            if normalised in df_col_set:
                detected[field] = normalised
                break

    return detected


# ─────────────────────────────────────────────────────────────────────────────
# Cleaning
# ─────────────────────────────────────────────────────────────────────────────

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    In-place-safe cleaning:
    - Fill NaN in text columns with empty string
    - Strip leading/trailing whitespace
    - Normalise status column if detected
    """
    df = df.copy()

    # Text columns: fill NaN + strip
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].fillna("").astype(str).apply(
        lambda col: col.str.strip()
    )

    # Replace "nan" strings left over from .astype(str) on NaN floats
    df[obj_cols] = df[obj_cols].replace("nan", "")

    return df


def normalise_status_column(df: pd.DataFrame, status_col: str) -> pd.DataFrame:
    """Map raw status values to human-readable names using STATUS_NORMALISE."""
    if status_col not in df.columns:
        return df
    df = df.copy()
    df[status_col] = (
        df[status_col]
        .str.lower()
        .map(lambda v: STATUS_NORMALISE.get(v, v.title()))
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Light sanity-check on the loaded DataFrame.

    Returns (is_ok, [warning/error messages])
    Errors start with "❌", warnings with "⚠️".
    """
    issues: list[str] = []

    if len(df) == 0:
        issues.append("❌ File has no data rows.")
    if len(df.columns) < 2:
        issues.append("❌ File has fewer than 2 columns – please check the format.")

    # Large file warning
    if len(df) > 5_000:
        issues.append(
            f"⚠️  Large file: {len(df):,} rows.  "
            "LLM mode may take several minutes – consider Keyword mode."
        )
    elif len(df) > 2_000:
        issues.append(
            f"⚠️  {len(df):,} rows detected.  "
            "LLM mode will take a few minutes."
        )

    # Completely empty columns
    empty = [
        c for c in df.columns
        if df[c].replace("", pd.NA).isna().all()
    ]
    if empty:
        issues.append(f"⚠️  Columns with no data: {', '.join(empty)}")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append(f"⚠️  {dup_count:,} duplicate row(s) found.")

    errors = [i for i in issues if i.startswith("❌")]
    return len(errors) == 0, issues


# ─────────────────────────────────────────────────────────────────────────────
# Filter helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_filter_options(df: pd.DataFrame, column: str) -> list[str]:
    """Return sorted unique non-empty string values of *column* for dropdowns."""
    if not column or column not in df.columns:
        return []
    vals = df[column].dropna().astype(str).str.strip()
    vals = vals[vals != ""].unique().tolist()
    return sorted(vals)


def apply_filters(
    df: pd.DataFrame,
    *,
    assignment_group: Optional[str] = None,
    status: Optional[str] = None,
    ticket_id: Optional[str] = None,
    category: Optional[list[str]] = None,
    assignment_group_col: Optional[str] = None,
    status_col: Optional[str] = None,
    id_col: Optional[str] = None,
    category_col: str = "Category",
) -> pd.DataFrame:
    """
    Apply UI filters to *df* and return the filtered subset.
    All filters are AND-combined.  "All" / empty string = no filter.
    """
    out = df.copy()

    if assignment_group and assignment_group != "All" and assignment_group_col and assignment_group_col in out.columns:
        out = out[
            out[assignment_group_col].astype(str)
            .str.contains(re.escape(assignment_group), case=False, na=False)
        ]

    if status and status != "All" and status_col and status_col in out.columns:
        out = out[
            out[status_col].astype(str).str.lower() == status.lower()
        ]

    if ticket_id and ticket_id.strip() and id_col and id_col in out.columns:
        out = out[
            out[id_col].astype(str)
            .str.contains(re.escape(ticket_id.strip()), case=False, na=False)
        ]

    if category and category_col in out.columns:
        out = out[out[category_col].isin(category)]

    return out


# keep re import at top
import re  # noqa: E402
