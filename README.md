# 🗺️ Maps Lead Scraper

> **Enterprise Lead Generation & Website Audit Platform**  
> Discover businesses globally, audit their web presence, and export client-ready reports — all from a single tool.

Built for **agency owners**, **web design freelancers**, and **SEO specialists** who need to identify high-value outreach opportunities at scale: businesses with no website, broken links, insecure HTTP, or non-mobile-friendly pages.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Global Business Search** | Query any city or country using the Google Places API |
| 🧪 **Automated Website Auditing** | 5-tier quality check: Active, Insecure, Broken, Not Mobile-Friendly, No Website |
| 📊 **SaaS Dashboard UI** | Dark-mode single-page interface with metric cards, tabbed filtering, and live search |
| 📤 **Instant Exports** | One-click export to CSV, TSV/Excel, and PDF report |
| 🤖 **Gemini AI Ready** | Quality score column scaffolded and ready for Gemini API integration |
| 🗄️ **Supabase Persistence** | Upserts leads to a Supabase `leads` table with duplicate prevention |
| 🔒 **Safe Fallback Modes** | Missing API keys trigger mock/logging mode — the app never crashes |
| ⚡ **FastAPI REST Backend** | Local API server with Swagger UI, CORS support, and JSON responses |

---

## 🏗️ Architecture Overview

```
User (Browser)
    │
    ▼
index.html  ──POST /api/run-pipeline──▶  server.py (FastAPI)
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                         scraper.py      auditor.py      database.py
                     (Google Places)  (HTTP/HTML Audit)  (Supabase)
```

---

## 📁 Project Structure

```
maps-lead-scraper/
│
├── index.html          # SaaS dashboard UI (HTML + CSS + Vanilla JS)
├── server.py           # FastAPI REST API server (entry point for web UI)
├── main.py             # CLI pipeline runner (Scrape → Audit → Persist → Report)
│
├── scraper.py          # Google Places API lead extraction module
├── auditor.py          # HTTP/HTML website quality audit engine
├── database.py         # Supabase persistence module (with mock fallback)
├── test_auditor.py     # Unit test suite for the audit engine
│
├── .env                # Environment variables (not committed to git)
├── .env.example        # Environment variable template
├── requirements.txt    # Python package dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- A Google Places API key *(optional — mock data used if absent)*
- A Supabase project *(optional — logging mode used if absent)*

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/maps-lead-scraper.git
cd maps-lead-scraper
```

---

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

**Activate the virtual environment:**

<table>
<tr><th>Platform</th><th>Command</th></tr>
<tr><td>Windows PowerShell</td><td><code>.\venv\Scripts\Activate.ps1</code></td></tr>
<tr><td>Windows CMD</td><td><code>.\venv\Scripts\activate.bat</code></td></tr>
<tr><td>macOS / Linux</td><td><code>source venv/bin/activate</code></td></tr>
</table>

You should see `(venv)` appear at the start of your terminal prompt.

---

### 3. Install Dependencies

```bash
pip install fastapi uvicorn requests bs4 python-dotenv supabase
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the example file and fill in your credentials:

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` with your actual values:

```env
GOOGLE_PLACES_API_KEY=YOUR_GOOGLE_PLACES_API_KEY
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_OR_ANON_KEY
```

> **Don't have API keys yet?** No problem — the app runs safely without them:
>
> | Missing Key | Behaviour |
> |---|---|
> | `GOOGLE_PLACES_API_KEY` | `scraper.py` falls back to built-in mock business data |
> | `SUPABASE_URL` / `SUPABASE_KEY` | `database.py` switches to **MOCK/LOGGING mode** — all saves are printed to the console instead |
>
> This means you can run and test the full pipeline end-to-end with zero external credentials.

---

## ▶️ Running the Application

### Option A — Web UI (Recommended)

**Step 1:** Start the FastAPI backend server:

```bash
python server.py
```

The API will be available at `http://127.0.0.1:8000`.

**Step 2:** Open the dashboard in your browser:

```
# Simply open the file directly:
index.html  →  double-click or drag into any browser

# Or use VS Code Live Server extension for hot reload
```

> Use the **Demo Mode** toggle in the top-right of the UI to load 12 offline mock leads instantly, without needing the server running.

---

### Option B — CLI Pipeline

Run the full scrape → audit → persist → report pipeline directly in the terminal:

```bash
python main.py
```

This outputs a formatted ASCII table of audited businesses to the console and persists results to Supabase (or logs them if in mock mode).

---

### Running Unit Tests

```bash
python test_auditor.py
```

The test suite covers audit edge cases including `None` URLs, plain HTTP, missing viewport tags, broken endpoints, and healthy HTTPS sites.

---

## 🌐 API Reference

Once `server.py` is running, visit the interactive Swagger UI:

```
http://127.0.0.1:8000/docs
```

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns API status |
| `GET` | `/api/leads` | Retrieve all persisted leads from Supabase |
| `POST` | `/api/run-pipeline` | Run scrape + audit pipeline for a given location and keyword |

### `POST /api/run-pipeline` — Request Body

```json
{
  "location": "Miami, FL",
  "keyword": "Plumbers"
}
```

### `POST /api/run-pipeline` — Response

```json
{
  "status": "success",
  "location": "Miami, FL",
  "keyword": "Plumbers",
  "records_processed": 5,
  "records_saved": 5,
  "leads": [
    {
      "business_name": "Apex Plumbing Experts",
      "phone_number": "+1 305-555-0192",
      "address": "123 Biscayne Blvd, Miami, FL",
      "website": "https://apexplumbing.com",
      "status_flag": "ACTIVE_WEBSITE"
    }
  ]
}
```

---

## 🏷️ Audit Status Reference

Each business website is audited using a strict 5-tier priority system. The **most severe issue** is always reported first.

| Status Flag | Colour | Meaning |
|---|---|---|
| `ACTIVE_WEBSITE` | 🟢 Emerald | Site is live, HTTPS, and mobile-friendly |
| `INSECURE_WEBSITE` | 🟡 Amber | Site uses plain `http://` — no SSL |
| `NOT_MOBILE_FRIENDLY` | 🔵 Sky Blue | Missing `<meta name="viewport">` tag |
| `BROKEN_WEBSITE` | 🔴 Rose | DNS failure, timeout, or HTTP 4xx/5xx |
| `NO_WEBSITE` | ⬜ Slate | No URL found for the business |

---

## 🗄️ Supabase Database Schema

Create the following table in your Supabase project:

```sql
CREATE TABLE leads (
  id             BIGSERIAL PRIMARY KEY,
  business_name  TEXT NOT NULL,
  phone_number   TEXT,
  address        TEXT,
  website        TEXT,
  status_flag    TEXT,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (business_name, address)
);
```

The `UNIQUE` constraint on `(business_name, address)` enables upsert logic — re-running the pipeline updates existing records instead of creating duplicates.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **API Framework** | FastAPI + Uvicorn |
| **Web Scraping** | Google Places API (Text Search + Place Details) |
| **Website Auditing** | `requests` + `BeautifulSoup4` |
| **Database** | Supabase (PostgreSQL) via `supabase-py` |
| **Frontend** | HTML5 + Vanilla JS + CSS Variables (Inter font) |
| **Config** | `python-dotenv` |

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
