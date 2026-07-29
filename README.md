# 🗺️ Maps Lead Scraper

> **Enterprise Lead Generation & Website Audit Platform**  
> Discover businesses globally, audit their web presence, and export client-ready reports.

Built for **agency owners**, **web design freelancers**, and **SEO specialists** who need to identify high-value outreach opportunities at scale: businesses with no website, broken links, insecure HTTP, or non-mobile-friendly pages.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Global Business Search** | Query any city or country using the Google Places API |
| 🧪 **Automated Website Auditing** | 5-tier quality check: Active, Insecure, Broken, Not Mobile-Friendly, No Website |
| 📊 **Royal Enterprise Dashboard** | Dark-mode SaaS UI with Royal Indigo/Sapphire theme, metric cards, tabbed filtering, and live search |
| 📤 **Instant Exports** | One-click export to CSV, TSV/Excel, and PDF report |
| 🤖 **Gemini AI Ready** | Quality score column scaffolded and ready for Gemini API integration |
| 🗄️ **Supabase Persistence** | Upserts leads to a Supabase `leads` table with duplicate prevention |
| 🔒 **Safe Fallback Mode** | Missing Supabase credentials trigger MOCK/LOGGING mode — the app never crashes |
| ⚡ **FastAPI REST Backend** | Local API server with Swagger UI, CORS support, and JSON responses |

> **Important:** A valid `GOOGLE_PLACES_API_KEY` in your `.env` file is required to fetch live business results. Without it, the pipeline returns no data.

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
├── index.html          # Royal Enterprise SaaS dashboard (HTML + CSS + Vanilla JS)
├── server.py           # FastAPI REST API server (entry point for web UI)
├── main.py             # CLI pipeline runner (Scrape → Audit → Persist → Report)
│
├── scraper.py          # Google Places API lead extraction module
├── auditor.py          # HTTP/HTML website quality audit engine
├── database.py         # Supabase persistence module (with MOCK/LOGGING fallback)
│
├── .env                # Environment variables (not committed to git)
├── .env.example        # Environment variable template
├── requirements.txt    # Python package dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── PROJECT_SUMMARY.md  # Full technical development history and handoff notes
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- A **Google Places API key** — required for live business results
- A Supabase project *(optional — MOCK/LOGGING mode used if absent)*

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

> **Credential Behaviour:**
>
> | Missing Key | Behaviour |
> |---|---|
> | `GOOGLE_PLACES_API_KEY` | Pipeline returns **no results** — the UI displays an empty state with instructions |
> | `SUPABASE_URL` / `SUPABASE_KEY` | `database.py` switches to **MOCK/LOGGING mode** — saves are printed to the console |

---

## ▶️ Running the Application

### Option A — Web UI (Recommended)

**Step 1:** Start the FastAPI backend server:

```bash
python server.py
```

The API will be running at `http://127.0.0.1:8000`.

**Step 2:** Open the dashboard — double-click `index.html` or open it in any browser:

```
index.html  →  open in browser (Chrome, Edge, Firefox)
```

---

### Option B — CLI Pipeline

Run the full scrape → audit → persist → report pipeline directly in the terminal:

```bash
python main.py
```

This outputs a formatted ASCII table of audited businesses to the console and persists results to Supabase (or logs them if in mock mode).

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

### `POST /api/run-pipeline` — Success Response

```json
{
  "status": "success",
  "location": "Miami, FL",
  "keyword": "Plumbers",
  "records_processed": 20,
  "records_saved": 20,
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

### `POST /api/run-pipeline` — No Results Response

```json
{
  "status": "no_results",
  "location": "Miami, FL",
  "keyword": "Plumbers",
  "records_processed": 0,
  "records_saved": 0,
  "leads": []
}
```

---

## 🏷️ Audit Status Reference

Each business website is evaluated using a strict 5-tier priority system. The **most severe issue is reported first**.

| Status Flag | Colour | Meaning |
|---|---|---|
| `ACTIVE_WEBSITE` | 🟢 Emerald `#10B981` | Site is live, HTTPS, and mobile-friendly |
| `INSECURE_WEBSITE` | 🟡 Amber Gold `#F59E0B` | Site uses plain `http://` — no SSL |
| `NOT_MOBILE_FRIENDLY` | ⬜ Royal Slate `#64748B` | Missing `<meta name="viewport">` tag |
| `BROKEN_WEBSITE` | 🔴 Crimson `#E11D48` | DNS failure, timeout, or HTTP 4xx/5xx |
| `NO_WEBSITE` | ◼ Muted Slate `#475569` | No URL found for the business |

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
| **Frontend** | HTML5 + Vanilla JS + CSS Variables (Inter font, Royal Enterprise Theme) |
| **Config** | `python-dotenv` |

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
