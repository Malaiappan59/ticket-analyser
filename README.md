# 🎫 IT Ticket Volume Dump Analyser

> Automatically classify 700+ ITSM tickets from **ServiceNow / Jira / Datadog / Splunk / SolarWinds** into structured categories using a local **Ollama LLM** or keyword rules — then export a colour-coded Excel report.

---

## 📋 Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Local Setup (Step-by-Step)](#local-setup)
5. [Install & Run Ollama](#install-ollama)
6. [Running the App](#running-the-app)
7. [Deploy on Streamlit Cloud (GitHub)](#deploy-on-streamlit-cloud)
8. [Input File Format](#input-file-format)
9. [Output Excel Format](#output-excel-format)
10. [Categories](#categories)
11. [Running Tests](#running-tests)
12. [Troubleshooting](#troubleshooting)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **LLM Classification** | Uses Ollama (llama3.2, mistral, etc.) for smart, context-aware classification |
| 🔑 **Keyword Fallback** | Rule-based keyword classifier when Ollama is offline — works 100% offline |
| 📥 **File Support** | Accepts `.csv`, `.xlsx`, `.xls` exports from any ITSM tool |
| 🗂️ **Auto Column Detection** | Auto-detects ticket ID, type, description, status, group columns |
| 🔍 **Smart Filters** | Filter by Assignment Group, Status, Ticket ID, and Category |
| 📊 **Visual Analytics** | Interactive bar + pie charts via Plotly |
| 📥 **Excel Export** | 3-sheet formatted Excel: Classified Tickets · All Tickets · Summary |
| ⚡ **700+ Tickets** | Batch processing with live progress bar and ETA |

---

## 🛠 Tech Stack

```
Python 3.10+      — Core language
Streamlit 1.35+   — Web UI framework
Ollama            — Local LLM server (llama3.2 recommended)
Pandas            — Data processing
Plotly            — Interactive charts
OpenPyXL          — Excel generation
Requests          — Ollama API calls
```

---

## 📁 Project Structure

```
ticket-analyser/
├── app.py                     ← Main Streamlit application (entry point)
├── requirements.txt           ← Python dependencies
├── .gitignore
├── README.md
├── .streamlit/
│   └── config.toml            ← Streamlit UI theme & server config
├── config/
│   ├── __init__.py
│   └── settings.py            ← Categories, Ollama config, column mappings
├── core/
│   ├── __init__.py
│   ├── classifier.py          ← LLM + keyword classification engine
│   ├── preprocessor.py        ← File loading, column detection, filtering
│   └── exporter.py            ← Excel 3-sheet output builder
├── utils/
│   ├── __init__.py
│   └── helpers.py             ← Sample data generator + misc utilities
├── sample_data/
│   └── generate_sample.py     ← Standalone script to generate test CSV
└── tests/
    ├── __init__.py
    └── test_cases.py          ← 40+ unit & integration tests
```

---

## 🖥 Local Setup

### Prerequisites

- Python **3.10 or higher**
- pip (comes with Python)
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ticket-analyser.git
cd ticket-analyser
```

### Step 2 — Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

You should see all packages install without errors.

---

## 🦙 Install & Run Ollama

Ollama runs a local LLM server on your machine.
*(Skip this section if you want Keyword-Only mode — it works without Ollama.)*

### macOS / Linux — one-liner

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows

Download the installer from **https://ollama.ai/download** and run it.

### Start the Ollama server

```bash
ollama serve
```

Leave this terminal open. Ollama runs on `http://localhost:11434`.

### Pull a model (first time only)

```bash
# Recommended: fast & accurate
ollama pull llama3.2

# Alternatives (heavier but more accurate)
ollama pull mistral
ollama pull llama3.1
```

### Verify Ollama is working

```bash
ollama list        # shows pulled models
ollama run llama3.2 "Say hello"
```

---

## ▶ Running the App

With your virtual environment activated:

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

### First-time workflow

1. The sidebar shows **✅ Ollama Running** (or **❌** if offline)
2. Click **"🔧 Generate sample 750-ticket CSV"** to get test data
3. Upload the CSV using the file uploader
4. Adjust column mappings if needed (auto-detected)
5. Click **"▶ Start Analysis"**
6. Switch to **"📊 Results & Export"** tab
7. Filter, explore, download Excel

---

## ☁️ Deploy on Streamlit Cloud (GitHub)

> Streamlit Cloud is **free** for public repos and deploys in ~2 minutes.
> Note: Ollama cannot run on Streamlit Cloud (no local GPU), so the deployed
> app will use **Keyword-Only** mode automatically.

### Step 1 — Push to GitHub

```bash
# From your project folder
git init
git add .
git commit -m "Initial commit: IT Ticket Volume Analyser"

# Create a repo on GitHub (github.com → New repository → ticket-analyser)
git remote add origin https://github.com/YOUR_USERNAME/ticket-analyser.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **"New app"**
4. Fill in:
   - **Repository:** `YOUR_USERNAME/ticket-analyser`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **"Deploy!"**

Streamlit Cloud will:
- Install packages from `requirements.txt` automatically
- Give you a public URL like `https://ticket-analyser.streamlit.app`

### Step 3 — Update the deployment

Every `git push` to `main` triggers an automatic redeploy:

```bash
git add .
git commit -m "Update: improved category keywords"
git push origin main
```

---

## 📊 Input File Format

Upload any `.csv` or `.xlsx` export from your ITSM tool.
Columns can be in any order — the app auto-detects them.

### Example ServiceNow Export (CSV)

```csv
Number,Type,Short_Description,Description,Caller_ID,Assignment_Group,Priority,Status,Domain,Work_Notes,Remarks
INC0001234,Incident,High CPU usage on PROD-APP-01,CPU utilization at 98% for 30 mins...,john.smith,L2-Server Team,P2 - High,In Progress,IT Infrastructure,...,
INC0001235,Incident,Oracle tablespace full,APP_DATA tablespace at 97%...,sarah.jones,L2-Database Admin,P1 - Critical,New,...,,
```

### Minimum required columns

At least **one** description column:
- `Short_Description` **or** `Description` **or** `Work_Notes`

Everything else (Status, Group, ID) is optional but enables filtering.

---

## 📤 Output Excel Format

The generated Excel file has **3 sheets**:

### Sheet 1: "Classified Tickets"
- Each **category is a column** (CPU, Memory, Storage … Others)
- Ticket IDs listed under their category column
- **`Total: N`** row at the bottom of each column
- Colour-coded column headers

### Sheet 2: "All Tickets (Classified)"
- Full original data with a prepended **`Category`** column
- Category cell is colour-coded per category
- Auto-filter enabled on all columns

### Sheet 3: "Category Summary"
- Category | Count | Percentage | Visual Bar
- Totals row
- Embedded **bar chart**

---

## 📂 Categories

| Category | Examples |
|----------|---------|
| **CPU** | High CPU, processor utilisation, CPU spike, vCPU saturation |
| **Memory** | OOM, heap space, RAM usage, memory leak, swap |
| **Storage** | Disk full, volume capacity, IOPS, RAID degraded |
| **Network** | Connectivity loss, VPN down, DNS failure, latency |
| **Hardware** | Fan failure, PSU fault, BIOS error, UPS battery |
| **Middleware** | WebLogic, Tomcat, Nginx, Kafka, RabbitMQ, Docker/K8s |
| **Application** | App crash, 500 error, deployment failure, batch job |
| **Database** | Oracle, MySQL, PostgreSQL, slow query, backup failure |
| **Security** | SSL cert expired, CVE, brute-force, account locked |
| **OS** | Kernel panic, BSOD, OS patch, zombie process, cron |
| **Monitoring** | Datadog alert, Splunk forwarder, SolarWinds node |
| **Others** | Anything that doesn't match above categories |

---

## 🧪 Running Tests

```bash
# Run all tests (verbose)
python -m pytest tests/test_cases.py -v

# Run a specific test class
python -m pytest tests/test_cases.py::TestKeywordClassifier -v

# Run without pytest (built-in runner)
python tests/test_cases.py
```

### Test coverage summary

| Test Class | Tests | What it covers |
|-----------|-------|----------------|
| `TestKeywordClassifier` | 12 | Best/worst keyword cases, empty, unicode, gibberish |
| `TestNormaliseCategory` | 7 | LLM response normalisation |
| `TestPreprocessorLoading` | 6 | CSV/Excel loading, encoding, BOM |
| `TestColumnDetection` | 3 | Auto-detect column mapping |
| `TestFiltering` | 7 | Filter combinations, edge cases |
| `TestValidation` | 5 | DataFrame validation rules |
| `TestExporter` | 5 | Excel generation, 3 sheets, 750 rows |
| `TestSampleDataGenerator` | 6 | Data quality, uniqueness, performance |
| `TestEndToEndPipeline` | 3 | Full pipeline integration test |

---

## 🔧 Troubleshooting

### "Ollama not running" in sidebar
```bash
# Make sure Ollama is started
ollama serve

# In a separate terminal, verify:
curl http://localhost:11434/api/tags
```

### "No module named 'streamlit'"
```bash
# Make sure your virtualenv is activated
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### App shows "Not Available" for all column mappings
Your column names don't match expected patterns.
→ Use the dropdowns on the right to manually map each column.

### LLM classification is very slow
- Switch to **"🔑 Keyword Only"** mode in the sidebar (instant, offline)
- Or use a smaller model: `ollama pull llama3.2:1b`

### Excel download doesn't work on Streamlit Cloud
The Excel is generated server-side and streamed to your browser.
Try a different browser or clear cache.

### "Disk quota exceeded" on Streamlit Cloud
Streamlit Cloud free tier has limits.
→ Reduce file size or upgrade to a paid plan.

---

## 📬 Extending the App

### Add a new category
Edit `config/settings.py` → `CATEGORIES` dict:
```python
"VMware": [
    "vmware", "esxi", "vsphere", "vcenter", "vmotion",
    "snapshot", "vsan", "nsx",
],
```
And add a colour in `CATEGORY_COLORS`.

### Change the Ollama model default
Edit `config/settings.py`:
```python
OLLAMA_CONFIG = {
    "default_model": "mistral",   # ← change here
    ...
}
```

### Increase upload size limit
Edit `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 500   # MB
```

---

## 📄 Licence

MIT — free to use, modify, and distribute.
