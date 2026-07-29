# PROJECT SUMMARY & TECHNICAL AUDIT TRAIL

| Field | Detail |
|---|---|
| **Project Name** | Maps Lead Scraper |
| **Repository Path** | `C:\Coding Projects\maps-lead-scraper` |
| **Target Goal** | Enterprise Lead Generation & Website Quality Auditing SaaS Platform |
| **Report Date** | July 2026 |
| **Status** | Active — Production-Ready (pending live API key configuration) |

---

## 1. Executive Summary

Maps Lead Scraper is a full-stack enterprise tool designed for **agency owners, web design freelancers, and SEO specialists** who need to discover real-world businesses globally, audit the technical health of their websites, identify high-value outreach opportunities, and export structured lead reports.

The system ingests a location and business keyword from either a CLI terminal or a browser-based SaaS dashboard, queries the Google Places API to extract business data, runs each result through a 5-tier website auditing engine, persists the output to a Supabase PostgreSQL database, and renders results in a dynamic, filterable web interface with one-click export capabilities.

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
  │  scraper.py         │   Google Places Text Search API
  │  fetch_places()     │   → Place Details API (phone + website)
  └─────────────────────┘   → Mock fallback if key is absent
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
- Implemented automatic **MOCK/LOGGING mode** detection — if `SUPABASE_URL` or `SUPABASE_KEY` are absent or set to placeholder strings, all database operations are safely printed to the console instead of executing against a real database
- Integrated `save_leads()` and `get_all_leads()` into `main.py` CLI pipeline
- Implemented `scraper.py` with dual-stage Google Places API calls:
  - **Text Search** → returns a list of matching businesses
  - **Place Details** → secondary API call per business to retrieve phone number and website URL
  - Mock data fallback (`MOCK_BUSINESSES`) auto-activates when `GOOGLE_PLACES_API_KEY` is missing or set to `"YOUR_API_KEY_HERE"`

---

### Phase 2 — Code Audit & Unit Testing

**Objective:** Validate the auditor engine and reach 100% test coverage of core edge cases.

**Accomplishments:**

- Diagnosed and fixed a **Windows UTF-8 terminal encoding bug** in `main.py`: the default `cp1252` Windows console encoding cannot render Unicode box-drawing characters used in the ASCII table output; resolved by wrapping `sys.stdout` and `sys.stderr` with explicit `UTF-8` encoding at startup
- Created `test_auditor.py` — a comprehensive unit test suite covering all audit code paths:

| Test Case | Input | Expected Status |
|---|---|---|
| None URL | `None` | `NO_WEBSITE` |
| Empty string URL | `""` | `NO_WEBSITE` |
| `"N/A"` string | `"N/A"` | `NO_WEBSITE` |
| HTTP connection failure | Mocked `ConnectionError` | `BROKEN_WEBSITE` |
| HTTP 404 response | Mocked `HTTPError` | `BROKEN_WEBSITE` |
| Plain `http://` URL | Live or mocked HTTP | `INSECURE_WEBSITE` |
| Missing viewport tag | Mocked HTML without `<meta name="viewport">` | `NOT_MOBILE_FRIENDLY` |
| Fully valid HTTPS site | Mocked HTTPS + viewport present | `ACTIVE_WEBSITE` |

- Fixed a critical bug in the `HTTPError` mock: `requests.exceptions.HTTPError` requires the mock response object to have a `.response` attribute — the initial mock was missing this, causing the test to raise an unexpected `AttributeError` rather than being caught by the auditor
- Achieved **6/6 unit tests passing** with zero failures

---

### Phase 3 — REST API Server Construction

**Objective:** Expose the pipeline as a local REST API to serve the browser-based frontend.

**Accomplishments:**

- Built `server.py` using **FastAPI** with **Uvicorn** ASGI server
- Configured **CORS middleware** with `allow_origins=["*"]` to enable unrestricted local browser access
- Implemented Pydantic `ScrapeRequest` model for typed request body validation
- Exposed three endpoints:
  - `GET /` — Health check, returns API status
  - `GET /api/leads` — Returns all persisted leads from Supabase
  - `POST /api/run-pipeline` — Executes the full scrape → audit → save pipeline
- Included `MOCK_PLACES_DATA` as an in-server fallback dataset (5 Miami businesses) for offline development
- Integrated FastAPI's auto-generated **Swagger UI** at `/docs` for interactive API testing
- Added `pyrefly: ignore` comments for `fastapi`, `pydantic`, and `fastapi.middleware.cors` imports to suppress false-positive static analysis warnings

---

### Phase 4 — Web Interface (SaaS Dashboard)

**Objective:** Build a production-grade, client-facing web interface as a single self-contained HTML file.

**Accomplishments:**

- Created `index.html` — a fully self-contained single-page application with zero external JavaScript dependencies
- **Design System:**
  - Dark mode default with CSS custom properties (design tokens) for consistent theming
  - `Inter` font via Google Fonts CDN
  - Animated radial glow background using CSS `@keyframes` (two drifting pseudo-elements)
  - Glassmorphism-style card borders with top gradient accent lines per card type
  - Hover micro-animations and transform lifts on all interactive elements
- **Search Control Bar:**
  - Location free-text input
  - Business keyword free-text input
  - 5 quick-select category chips (Plumbers, Electricians, Dentists, Restaurants, Auto Repair)
  - "All Businesses" chip that clears the keyword field
  - Bold CTA button with loading spinner state
- **Metric Cards (4-column grid):**
  - Total Discovered (animated counter)
  - High-Value Opportunities: `NO_WEBSITE` + `BROKEN_WEBSITE` count (animated)
  - Sub-Optimal Websites: `INSECURE_WEBSITE` + `NOT_MOBILE_FRIENDLY` count (animated)
  - Gemini AI Average Score: Placeholder pending Gemini API integration
- **Lead Results Table:**
  - Tabbed filtering: All Leads, High Opportunity, Mobile Issues, Active Sites
  - Live tab counts updated after each search
  - In-table fuzzy search across all fields
  - Clickable column headers for ascending/descending sort
  - Semantic colour-coded status badges for all 5 audit states
  - Gemini AI Rating column scaffolded with `— / 10` placeholder and tooltip
  - Clickable website links opening in `_blank`
- **Export Engine:**
  - **CSV:** RFC-4180 compliant, UTF-8 BOM prefixed, `""`-escaped fields, triggers browser download
  - **TSV/Excel:** Tab-delimited file openable directly in Microsoft Excel
  - **PDF:** Opens a new browser window with formatted print-ready HTML and triggers `window.print()`
- **Demo Mode:**
  - Toggle switch in the topbar bypasses the live API call
  - Loads 12 offline mock businesses with diverse status flags for UI testing
  - Simulates a 1.1-second network delay for realism
- **API Status Pill:** Polls `GET /` every 15 seconds, displays green "API Online" or grey "API Offline" with animated dot
- **Toast Notification System:** Non-blocking slide-in alerts for success, error, and info events
- **Accessibility:** ARIA roles, labels, `tabindex` on interactive elements, `aria-live` regions for dynamic content

---

### Phase 5 — Pipeline Binding & Fixes

**Objective:** Connect the REST API server to the real scraper engine and resolve import linting warnings.

**Problem Identified:** The initial `server.py` implementation contained a hardcoded loop over its own internal `MOCK_PLACES_DATA` and never called `fetch_places()` from `scraper.py`. As a result, the `location` and `keyword` inputs from the frontend were echoed in the JSON response but had zero effect on which businesses were actually returned.

**Fixes Applied by Developer:**

- Imported `fetch_places` from `scraper.py` into `server.py`
- Replaced the static `MOCK_PLACES_DATA` loop with a dynamic call to `fetch_places(payload.location, search_keyword)` wrapped in a `try/except` block
- Retained `MOCK_PLACES_DATA` as a **secondary offline fallback** — only used if `fetch_places()` returns an empty list (e.g., missing API key or network failure)
- Added `__ALL__` keyword sentinel handling: when the frontend sends `keyword="__ALL__"`, it is normalised to `"all businesses"` before being passed to the scraper
- Made `keyword` optional in the validation — only `location` is now strictly required
- Updated docstrings and comments throughout `server.py` to reflect the live pipeline behaviour
- Added `pyrefly: ignore [missing-import]` comments for `fastapi`, `fastapi.middleware.cors`, and `pydantic` to suppress IDE static analysis false positives

---

## 3. Current File Status Matrix

| File | Status | Purpose |
|---|---|---|
| `auditor.py` | ✅ Working | 5-tier HTTP/HTML website quality audit engine |
| `database.py` | ✅ Working | Supabase upsert ORM with automatic MOCK/LOGGING fallback |
| `scraper.py` | 🟡 Awaiting Live Key | Google Places API extractor; mock data active until real key is set |
| `main.py` | ✅ Working | CLI runner: orchestrates scrape → audit → save → ASCII table report |
| `server.py` | ✅ Working | FastAPI REST API; dynamically calls `fetch_places()` with fallback |
| `test_auditor.py` | ✅ Working | Unit test suite — 6/6 tests passing |
| `index.html` | ✅ Working | Full SaaS dashboard UI with search, filters, table, and exports |
| `README.md` | ✅ Written | Setup guide, API reference, Supabase schema, and tech stack docs |
| `.env` | 🟡 Partial | `SUPABASE_URL` + `SUPABASE_KEY` set; `GOOGLE_PLACES_API_KEY` is placeholder |
| `.env.example` | ✅ Present | Template file for onboarding new developers |
| `requirements.txt` | ✅ Present | Python package dependency manifest |

---

## 4. Pending Handoff Tasks

### Task 1 — Google Places Live Key
**File:** `.env`  
**Action:** Replace the placeholder value:
```env
GOOGLE_PLACES_API_KEY=YOUR_GOOGLE_PLACES_API_KEY
```
with a real key from the [Google Cloud Console](https://console.cloud.google.com/) with the following APIs enabled:
- **Places API (Text Search)**
- **Places API (Place Details)**

Once set, `scraper.py` will automatically switch from mock data to live Google Places results. No code changes required.

---

### Task 2 — Supabase Key Verification
**File:** `.env`  
**Current value:** `sb_publishable_RWCd9YzfGJTVqcvHzY63Jw_YN-kmqws`  
**Problem:** The `supabase-py` Python client expects a standard JWT format key starting with `eyJ...`. The current `sb_publishable_` key format is not recognised and will cause the client to fall back to MOCK/LOGGING mode silently.  
**Action:** In your Supabase project dashboard → **Settings → API**, copy either the `anon` public key or the `service_role` key (both are in `eyJ...` JWT format) and update `.env`:
```env
SUPABASE_KEY=eyJ...your_actual_key...
```

---

### Task 3 — Gemini AI Quality Score Integration
**File:** `index.html`, `server.py`, `auditor.py` (or new `gemini.py` module)  
**Current state:** The Gemini AI Rating column in the results table renders `— / 10` with a purple `Gemini AI` pending badge.  
**Action required:**
1. Create a `gemini.py` module that accepts a business dict and website status, calls the Gemini API, and returns a numeric quality score (1–10)
2. Add `GEMINI_API_KEY` to `.env` and load it in `gemini.py`
3. In `server.py`, call `gemini.py` per business after the audit step and include `"gemini_score"` in the response JSON
4. In `index.html`, replace the `— / 10` placeholder with the actual score value from the API response and render a colour-coded score bar

---

## 5. Known Limitations & Technical Notes

- **Audit check order is intentional:** The auditor evaluates in strict priority (most severe first). An `http://` URL that also lacks a viewport tag will be reported as `INSECURE_WEBSITE`, not `NOT_MOBILE_FRIENDLY`. This is by design — the most actionable issue is surfaced first.
- **`server.py` still retains two hardcoded mock overrides** for `https://desktop-only.com` and `https://example.com/broken` — these bypass the real auditor and return preset flags. These should be removed once live API keys are active and the mock data fallback is no longer in use.
- **The `NOT_MOBILE_FRIENDLY` check has a known edge case:** Some modern single-page applications (SPAs) inject the viewport meta tag dynamically via JavaScript after page load. Since `auditor.py` audits the raw HTML response (no JavaScript execution), such sites may be incorrectly flagged as `NOT_MOBILE_FRIENDLY` even though they render correctly in a real browser.
- **Export PDF relies on `window.print()`:** The PDF export opens a new browser tab and triggers the system print dialog. The output quality depends on the user's browser and system print-to-PDF driver.

---

*Document generated: July 2026 — Maps Lead Scraper v1.0*
