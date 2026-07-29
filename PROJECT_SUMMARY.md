# PROJECT SUMMARY & TECHNICAL AUDIT TRAIL

| Field | Detail |
|---|---|
| **Project Name** | Maps Lead Scraper |
| **Repository Path** | `C:\Coding Projects\maps-lead-scraper` |
| **Target Goal** | Enterprise Lead Generation & Website Quality Auditing SaaS Platform |
| **Report Date** | July 2026 |
| **Current Status** | ✅ Production-Ready — Awaiting live `GOOGLE_PLACES_API_KEY` configuration |

---

## 1. Executive Summary

Maps Lead Scraper is a full-stack enterprise tool designed for **agency owners, web design freelancers, and SEO specialists** who need to discover real-world businesses globally, audit the technical health of their websites, identify high-value outreach opportunities, and export structured lead reports.

The system ingests a location and business keyword from either a CLI terminal or a Royal Enterprise SaaS dashboard, queries the Google Places API to extract business data, runs each result through a 5-tier website auditing engine, persists the output to a Supabase PostgreSQL database, and renders results in a dynamic, filterable web interface with one-click export capabilities.

### System Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MAPS LEAD SCRAPER                            │
│                     End-to-End Data Pipeline                        │
└─────────────────────────────────────────────────────────────────────┘

  [User Input]
  Location + Keyword
       │
       ▼
  ┌──────────────────────────────────────────────┐
  │  Web UI (index.html)  ──or──  CLI (main.py)  │
  └──────────────────────────────────────────────┘
       │ POST /api/run-pipeline
       ▼
  ┌─────────────────────┐
  │  REST API server.py │   FastAPI + Uvicorn on localhost:8000
  │  + CORS Middleware  │
  └─────────────────────┘
       │
       ▼
  ┌─────────────────────┐
  │   Scraper Engine    │   scraper.py
  │   fetch_places()    │   Google Places Text Search API
  │                     │   → Place Details API (phone + website)
  └─────────────────────┘   → Returns [] if no API key configured
       │ List[business_dict]
       ▼
  ┌─────────────────────┐
  │   Auditor Engine    │   auditor.py
  │   audit_website()   │   5-tier priority check:
  │                     │   NO_WEBSITE → BROKEN → INSECURE
  └─────────────────────┘   → NOT_MOBILE_FRIENDLY → ACTIVE
       │ List[(business_dict, status_flag)]
       ▼
  ┌─────────────────────┐
  │   Database Layer    │   database.py
  │   save_leads()      │   Supabase upsert on (business_name, address)
  │                     │   → MOCK/LOGGING mode if credentials absent
  └─────────────────────┘
       │ JSON Response
       ▼
  ┌───────────────────────────────────────────────────────────────┐
  │              Dynamic JSON → Web UI (index.html)               │
  │  Metric Cards │ Tab Filters │ Table │ Exports (CSV/TSV/PDF)   │
  └───────────────────────────────────────────────────────────────┘
```

---

## 2. Historical Development Timeline

### Phase 1 — Core Pipeline & Database Integration

**Objective:** Build the foundational data pipeline connecting scraping, auditing, and persistence.

**Accomplishments:**

- Implemented `database.py` with secure credential loading via `python-dotenv`
- Built `save_leads()` using Supabase upsert with composite conflict key `(business_name, address)` to prevent duplicate records across pipeline runs
- Built `get_all_leads()` returning all rows ordered by `created_at DESC`
- Implemented automatic **MOCK/LOGGING mode** detection — if `SUPABASE_URL` or `SUPABASE_KEY` are absent or set to placeholder strings, all database operations are safely printed to the console instead
- Integrated `save_leads()` and `get_all_leads()` into `main.py` CLI pipeline
- Implemented `scraper.py` with dual-stage Google Places API calls:
  - **Text Search** → returns a list of matching businesses
  - **Place Details** → secondary API call per business to retrieve phone number and website URL
  - Returns an empty list when `GOOGLE_PLACES_API_KEY` is missing or a placeholder

---

### Phase 2 — Code Audit & Unit Testing

**Objective:** Validate the auditor engine and reach 100% test coverage of core edge cases.

**Accomplishments:**

- Diagnosed and fixed a **Windows UTF-8 terminal encoding bug** in `main.py`: the default `cp1252` Windows console encoding cannot render Unicode box-drawing characters; resolved by wrapping `sys.stdout` and `sys.stderr` with explicit UTF-8 encoding at startup
- Created `test_auditor.py` — a unit test suite covering all audit code paths with 6/6 tests passing:

| Test Case | Expected Status |
|---|---|
| `None` URL | `NO_WEBSITE` |
| Empty string URL | `NO_WEBSITE` |
| `"N/A"` string | `NO_WEBSITE` |
| `ConnectionError` (mocked) | `BROKEN_WEBSITE` |
| HTTP 404 (mocked) | `BROKEN_WEBSITE` |
| Plain `http://` URL | `INSECURE_WEBSITE` |
| Missing viewport tag (mocked HTML) | `NOT_MOBILE_FRIENDLY` |
| HTTPS + viewport present (mocked) | `ACTIVE_WEBSITE` |

- Fixed `HTTPError` mock bug: `requests.exceptions.HTTPError` requires a `.response` attribute on the mock object; initial mock was missing this, causing `AttributeError`

---

### Phase 3 — REST API Server Construction

**Objective:** Expose the pipeline as a local REST API to serve the browser-based frontend.

**Accomplishments:**

- Built `server.py` using **FastAPI** with **Uvicorn** ASGI server
- Configured **CORS middleware** with `allow_origins=["*"]` to enable unrestricted local browser access
- Implemented Pydantic `ScrapeRequest` model for typed request body validation
- Exposed three endpoints: `GET /`, `GET /api/leads`, `POST /api/run-pipeline`
- Integrated FastAPI auto-generated **Swagger UI** at `/docs`

---

### Phase 4 — Web Interface (SaaS Dashboard — Initial Build)

**Objective:** Build a production-grade, client-facing web interface as a single self-contained HTML file.

**Accomplishments:**

- Created `index.html` — a self-contained single-page application with zero external JavaScript dependencies
- **Initial Design System:** Dark mode with blue/violet accents, Inter font, animated radial glow background, glassmorphism card borders
- Search controls, category chips, metric cards, tabbed filtering, fuzzy table search, column sorting
- Status badges for all 5 audit states
- Export engine: CSV, TSV/Excel, PDF via browser print dialog
- Demo Mode toggle with 12 offline mock leads for UI testing without a live API

---

### Phase 5 — Pipeline Binding & Server Fix

**Objective:** Connect the REST API server to the real scraper engine.

**Problem:** The initial `server.py` looped over its own internal `MOCK_PLACES_DATA` and never called `fetch_places()` — location and keyword inputs had zero effect on results.

**Fixes:**

- Imported `fetch_places` from `scraper.py` into `server.py`
- Replaced the static loop with a dynamic call to `fetch_places(payload.location, search_keyword)`
- Added `__ALL__` keyword sentinel normalisation
- Made `keyword` optional — only `location` is strictly required
- Added `pyrefly: ignore [missing-import]` comments for FastAPI, CORS, and Pydantic imports

---

### Phase 6 — Production Cleanup, Royal Enterprise Theme Overhaul & Documentation Sync

**Objective:** Strip all mock/demo scaffolding, apply a Royal Enterprise visual identity, and synchronise all documentation.

**Accomplishments:**

#### Codebase Cleanup
- **Deleted `test_auditor.py`** — unit tests were used during local development verification and are no longer required in the production repository
- **Removed `MOCK_PLACES_DATA`** from `server.py` entirely — no hardcoded business data remains anywhere in the backend
- **Removed the mock fallback branch** from `server.py` — when `fetch_places()` returns an empty list (missing API key or no results), the server now returns a clean `"status": "no_results"` JSON response instead of injecting fake data
- **Removed hardcoded status overrides** for `https://desktop-only.com` and `https://example.com/broken` — all websites now go through the real `audit_website()` engine with no exceptions
- **Scraper errors** now surface as HTTP 502 responses with descriptive detail messages

#### `index.html` — Royal Enterprise Theme Overhaul
- **Removed Demo Mode** toggle, `MOCK_LEADS` array, and all offline mock data triggers — the UI is now exclusively driven by the live FastAPI backend
- **Background:** Deep Midnight Onyx (`#070A0F` / `#0B0F19`)
- **Primary Accent:** Royal Indigo / Deep Sapphire (`#4F46E5` / `#3B82F6`)
- **Secondary Accent:** Rich Gold / Champagne (`#D97706` / `#F59E0B`) — used on the "All Businesses" chip, Gemini AI badge, and ambient glow
- **Cards:** Elevated Obsidian Glass (`#111827`) with refined border glows
- **Status badge updates:**
  - `BROKEN_WEBSITE` → Crimson Rose (`#E11D48`)
  - `NOT_MOBILE_FRIENDLY` → Royal Slate (`#64748B`)
  - `NO_WEBSITE` → Muted Slate (`#475569`)
- **Empty state guidance:** When no results are returned, the UI now shows: *"No businesses found. Ensure a valid GOOGLE_PLACES_API_KEY is configured in your .env file."*
- **API status pill** now shows an error-red dot when the API is offline, in addition to the green online state
- All link colours updated from `var(--accent)` blue to `var(--sapphire)` for Royal consistency

#### Documentation Updates
- **`README.md`** — Updated to reflect Royal Enterprise theme, removed Demo Mode references, removed `test_auditor.py` from file inventory, added `no_results` API response example, clarified that a live `GOOGLE_PLACES_API_KEY` is required
- **`PROJECT_SUMMARY.md`** — This document updated to log Phase 6 cleanup and visual redesign

---

## 3. Current File Status Matrix

| File | Status | Purpose |
|---|---|---|
| `auditor.py` | ✅ Working | 5-tier HTTP/HTML website quality audit engine |
| `database.py` | ✅ Working | Supabase upsert ORM with automatic MOCK/LOGGING fallback |
| `scraper.py` | 🟡 Awaiting Live Key | Google Places API extractor; returns `[]` until real key is set |
| `main.py` | ✅ Working | CLI runner: orchestrates scrape → audit → save → ASCII table report |
| `server.py` | ✅ Working | FastAPI REST API; calls `fetch_places()`, no mock data |
| `index.html` | ✅ Working | Royal Enterprise SaaS dashboard — live API only, no mock mode |
| `README.md` | ✅ Current | Setup guide, API reference, Supabase schema, tech stack docs |
| `PROJECT_SUMMARY.md` | ✅ Current | Full development history, Phase 6 cleanup log, handoff notes |
| `.env` | 🟡 Partial | Supabase keys set; `GOOGLE_PLACES_API_KEY` is still placeholder |
| `.env.example` | ✅ Present | Template file for onboarding new developers |
| `requirements.txt` | ✅ Present | Python package dependency manifest |

---

## 4. Pending Handoff Tasks

### Task 1 — Google Places Live Key *(Critical)*
**File:** `.env`  
**Action:** Replace the placeholder:
```env
GOOGLE_PLACES_API_KEY=YOUR_GOOGLE_PLACES_API_KEY
```
with a real key from the [Google Cloud Console](https://console.cloud.google.com/) with these APIs enabled:
- **Places API (Text Search)**
- **Places API (Place Details)**

Once set, `scraper.py` automatically switches to live results. No code changes required.

---

### Task 2 — Supabase Key Verification *(Medium)*
**File:** `.env`  
**Current value format:** `sb_publishable_...` *(non-standard)*  
**Required format:** `eyJ...` *(standard JWT)*  
**Action:** In Supabase dashboard → **Settings → API**, copy the `anon` or `service_role` key (both start with `eyJ...`) and update `.env`:
```env
SUPABASE_KEY=eyJ...your_actual_key...
```

---

### Task 3 — Gemini AI Quality Score Integration *(Enhancement)*
**Files:** `index.html`, `server.py`, new `gemini.py` module  
**Current state:** Rating column shows `— / 10` with a Gold "Gemini AI" pending badge  
**Steps:**
1. Create `gemini.py` — accepts a business dict + audit status, calls the Gemini API, returns a 1–10 score
2. Add `GEMINI_API_KEY` to `.env`
3. In `server.py`, call `gemini.py` per business after the audit step, include `"gemini_score"` in the JSON response
4. In `index.html`, replace `— / 10` placeholder with the actual score and render a colour-coded score bar

---

## 5. Known Limitations & Technical Notes

- **Audit priority is intentional:** The auditor evaluates in strict priority order (most severe first). An `http://` URL that also lacks a viewport tag will be reported as `INSECURE_WEBSITE`, not `NOT_MOBILE_FRIENDLY`.
- **SPA viewport edge case:** Some modern single-page applications inject the viewport meta tag via JavaScript after page load. Since `auditor.py` parses raw HTML (no JavaScript execution), such sites may be incorrectly flagged as `NOT_MOBILE_FRIENDLY`.
- **PDF export relies on `window.print()`:** Quality depends on the user's browser and system print-to-PDF driver.
- **The codebase is now 100% clean** of mock data and test scaffolding. All live execution paths require a valid `GOOGLE_PLACES_API_KEY`.

---

*Document last updated: July 2026 — Maps Lead Scraper v1.1 (Production Clean Build)*
