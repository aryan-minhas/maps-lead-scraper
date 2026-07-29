# 🚀 Master Implementation Plan & Integration Guide

**Target Developer:** Rayyan  
**Project:** Maps Lead Scraper (`maps-lead-scraper`)  
**Objective:** Finalize Production Integration — Google Places API + Gemini AI Rating Engine + Supabase Sync

---

## 📌 Important: Instructions for the AI / LLM

> [!IMPORTANT]
> **Mandatory Rules for the AI Assistant — Read Before Every Phase:**
>
> 1. **VERIFICATION GATEWAY:** BEFORE writing code, refactoring files, or executing any technical task, you **MUST explicitly ask Rayyan to confirm he has completed the required Manual Setup steps** for that phase. Do NOT write code or proceed until Rayyan explicitly confirms.
> 2. **NO MOCK DATA:** Do NOT re-introduce mock data arrays or demo toggles into `server.py` or `index.html`. The codebase is stripped of all mock datasets.
> 3. **PRESERVE ZERO-STATE HANDLING:** If `fetch_places` returns zero results or fails, `server.py` must return `"status": "no_results"` cleanly so `index.html` shows the setup guidance empty state.
> 4. **FOLLOW ARCHITECTURAL LAYERING:**
>    - `scraper.py` — Google Places API HTTP calls
>    - `auditor.py` — Website auditing (SSL, 404s, mobile tags) + Gemini AI ratings
>    - `database.py` — Supabase persistence via composite upsert
>    - `server.py` — Pipeline orchestration and REST API
>    - `index.html` — UI rendering with zero hardcoded leads

---

## 🛠️ Workflow Overview

Rayyan alternates between **Manual Setup** (API dashboards, keys, `.env`) and **AI Execution** (prompting the LLM to write integration code).

```
[ PHASE 1: MANUAL ]    ──►  Acquire Google Places API Key & update .env
        │
        ▼
[ AI VERIFICATION ]    ──►  AI asks: "Have you updated .env with Google Places Key?"
        │
        ▼
[ PHASE 2: AI CODE ]   ──►  AI verifies and polishes scraper.py
        │
        ▼
[ PHASE 3: MANUAL ]    ──►  Test live scraper locally via server.py + index.html
        │
        ▼
[ PHASE 4: MANUAL ]    ──►  Acquire Gemini API Key & update .env
        │
        ▼
[ AI VERIFICATION ]    ──►  AI asks: "Have you added GEMINI_API_KEY to .env?"
        │
        ▼
[ PHASE 5: AI CODE ]   ──►  AI implements Gemini AI 1–10 Rating Engine
        │
        ▼
[ PHASE 6: MANUAL ]    ──►  Acquire Supabase JWT Key & update .env
        │
        ▼
[ PHASE 7: MANUAL ]    ──►  Final end-to-end verification & production launch
```

---

## 📍 Phase 1 — Google Places API Setup (Manual)

### Step 1.1 — Obtain Your API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named **`Maps-Lead-Scraper`**
3. Navigate to **APIs & Services → Library**
4. Search for **Places API (New)** or **Places API** and click **Enable**
5. Navigate to **APIs & Services → Credentials**
6. Click **Create Credentials → API Key**
7. Copy the generated API key
8. *(Recommended)* Click **Restrict Key** → restrict usage to **Places API** only

### Step 1.2 — Update `.env`

Open `.env` in the project root and paste your live key:

```env
GOOGLE_PLACES_API_KEY=AIzaSyYourActualGooglePlacesKeyHere
```

> [!NOTE]
> Do not share this key publicly or commit it to Git. The `.gitignore` already excludes `.env`.

---

## 💻 Phase 2 — Google Places API Verification (AI Execution)

> [!IMPORTANT]
> **AI Checkpoint:** The AI assistant **must ask Rayyan** if Phase 1 is complete before writing any code.

Copy and paste the following prompt to your AI assistant (Claude / ChatGPT / Cursor):

```
PROMPT FOR AI:

Before writing any code, confirm that I have completed Phase 1 Manual Setup
and updated .env with a live GOOGLE_PLACES_API_KEY.

Once I confirm, inspect scraper.py and ensure:
1. It loads GOOGLE_PLACES_API_KEY from .env via python-dotenv correctly.
2. It sends an HTTP request to the Google Places Text Search API endpoint
   using the location and keyword parameters.
3. It makes a secondary Place Details API call per result to retrieve
   phone_number and website.
4. It parses responses into a list of dicts with keys:
   business_name, phone_number, address, website.
5. If a business has no website, website is set to None.
6. If the API returns 0 results, return an empty list [].
   Do NOT add any fallback mock data or dummy lists.
```

---

## 🧪 Phase 3 — Live Scraper Verification (Manual Test)

1. Open a terminal inside `(venv)` and start the API server:

   ```bash
   python server.py
   ```

2. Open `index.html` in your browser (double-click or drag into Chrome/Edge)

3. Enter a real search:
   - **Location:** `Austin, TX`
   - **Keyword:** `Dentists`

4. Click **Search & Audit Leads**

5. ✅ Verify that real Austin businesses appear in the Royal Enterprise table with correct audit status badges

> [!TIP]
> Check the terminal running `server.py` — you should see live `[INFO] auditor` log lines for each website being audited in real time.

---

## 🤖 Phase 4 — Gemini API Setup (Manual)

### Step 4.1 — Obtain Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Log in with your Google account
3. Click **Get API Key → Create API Key in new project**
4. Copy the generated Gemini API key

### Step 4.2 — Update `.env`

```env
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
```

---

## 💻 Phase 5 — Gemini AI Rating Engine (AI Execution)

> [!IMPORTANT]
> **AI Checkpoint:** The AI assistant **must ask Rayyan** if Phase 4 is complete and `GEMINI_API_KEY` has been added to `.env` before writing any code.

Copy and paste the following prompt to your AI assistant:

```
PROMPT FOR AI:

First, ask me if I have completed Phase 4 Manual Setup and added
GEMINI_API_KEY to .env. Once I confirm, proceed with this task:

Integrate the Google Gemini API to evaluate scraped websites and return
a Quality Rating score from 1 to 10.

Requirements:

1. In auditor.py (or a new module gemini_evaluator.py), create a function:
      rate_website_quality(url: str | None, status_flag: str) -> int

   Logic:
   - If status_flag is 'NO_WEBSITE'    → return 0 immediately
   - If status_flag is 'BROKEN_WEBSITE' → return 1 immediately
   - For all other statuses, call the Gemini 1.5 Flash API with:

     "Evaluate this website: URL={url}, Audit Status={status_flag}.
      Rate its quality from 1 to 10 based on security (HTTPS),
      mobile-friendliness, and overall usability.
      Return ONLY a single integer between 1 and 10."

   - Parse the integer from Gemini's response.
   - Wrap the entire Gemini call in try/except — return 5 as a safe
     fallback if the API fails, times out, or returns an unparseable value.

2. In server.py, call rate_website_quality() after audit_website() for
   each business and include 'gemini_score' (int) in the response JSON.

3. In index.html, update the 'Gemini AI Rating' column:
   - If gemini_score is present and > 0: render 'Score: X / 10' with a
     gold score badge, replacing the grey 'Pending' badge.
   - Colour-code the score: 1–3 crimson, 4–6 amber, 7–10 emerald.
   - Update the CSV, TSV, and PDF exports to include the Gemini score column.

Do NOT introduce mock scores or hardcoded fallback lead data.
```

---

## 💾 Phase 6 — Supabase Production Database (Manual)

### Step 6.1 — Obtain Your Supabase Key

1. Log in to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Project Settings → API**
4. Copy the **Project URL** and the **`anon` public key** (or `service_role` key for admin writes)

> [!NOTE]
> Standard Supabase JWT keys begin with `eyJ...`. If your key starts with `sb_publishable_`, it is the wrong format — use the JWT key from the API settings page instead.

### Step 6.2 — Update `.env`

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 6.3 — Verify Database Table Exists

Run this SQL in the Supabase **SQL Editor** if the `leads` table does not already exist:

```sql
CREATE TABLE IF NOT EXISTS leads (
  id             BIGSERIAL PRIMARY KEY,
  business_name  TEXT NOT NULL,
  phone_number   TEXT,
  address        TEXT,
  website        TEXT,
  status_flag    TEXT,
  gemini_score   INTEGER,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (business_name, address)
);
```

---

## 🏁 Phase 7 — Final End-to-End Verification (Manual)

Perform this checklist to confirm all systems are fully operational:

### 1. Start the API Server

```bash
python server.py
```

### 2. Run a Live Search

- Open `index.html` in your browser
- **Location:** `London, UK`
- **Keyword:** `Restaurants`
- Click **Search & Audit Leads**

### 3. Verification Checklist

- [ ] Real London restaurants appear in the results table
- [ ] Audit status badges display correctly (`ACTIVE_WEBSITE`, `INSECURE_WEBSITE`, `BROKEN_WEBSITE`, `NO_WEBSITE`, `NOT_MOBILE_FRIENDLY`)
- [ ] Gemini AI Rating column shows real `Score: X / 10` values (colour-coded)
- [ ] Metric cards update correctly (Total, High Opportunity, Sub-Optimal)

### 4. Check Database Persistence

- Log in to your [Supabase SQL Editor](https://supabase.com/dashboard)
- Run: `SELECT * FROM leads ORDER BY created_at DESC LIMIT 20;`
- [ ] Confirm rows are saved with correct `status_flag` and `gemini_score` values

### 5. Test Exports

- [ ] **CSV** — downloads and opens correctly with all columns including Gemini score
- [ ] **Excel / TSV** — opens in Microsoft Excel with correct formatting
- [ ] **PDF** — print dialog opens with a clean, structured lead report

---

## 🎉 Production Launch Ready

Once all 7 phases are complete, the **Maps Lead Scraper** platform will be fully operational with:

| Capability | Status |
|---|---|
| 🔍 Live global business discovery | ✅ Google Places API |
| 🧪 Automated website quality auditing | ✅ auditor.py |
| 🤖 AI-powered quality scoring | ✅ Gemini 1.5 Flash |
| 🗄️ Cloud database persistence | ✅ Supabase PostgreSQL |
| 📤 Client-ready report exports | ✅ CSV / Excel / PDF |

---

*Maps Lead Scraper — Integration Plan v1.0 · July 2026*
