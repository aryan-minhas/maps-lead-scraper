"""
server.py
---------
Local REST API server exposing lead scraping and auditing endpoints.
Connects directly to scraper.py (Google Places) and auditor.py.
"""

from typing import Any, Dict, List

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from database import get_all_leads, save_leads
from auditor import audit_website
from scraper import fetch_places

app = FastAPI(
    title="Maps Lead Scraper API",
    description="API for Lead Generation & Website Quality Auditing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    location: str
    keyword: str


@app.get("/")
def read_root() -> Dict[str, str]:
    """Healthcheck endpoint."""
    return {"status": "online", "message": "Lead Scraper API running"}


@app.get("/api/leads")
def fetch_leads() -> Dict[str, Any]:
    """Retrieve all leads stored in the database."""
    leads = get_all_leads()
    return {"status": "success", "count": len(leads), "leads": leads}


@app.post("/api/run-pipeline")
def run_pipeline(payload: ScrapeRequest) -> Dict[str, Any]:
    """
    Run the end-to-end scraper pipeline:
    1. Fetch businesses via Google Places API (scraper.py)
    2. Audit each website (auditor.py)
    3. Persist results to Supabase (database.py)
    4. Return structured JSON response
    """
    if not payload.location:
        raise HTTPException(status_code=400, detail="Location is required.")

    search_keyword = (
        payload.keyword
        if payload.keyword and payload.keyword.strip() not in ("", "__ALL__")
        else "businesses"
    )

    # Step 1: Fetch business leads from Google Places
    try:
        businesses = fetch_places(payload.location, search_keyword)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Scraper error: {exc}",
        )

    # Return empty result if no businesses found (e.g. missing API key)
    if not businesses:
        return {
            "status": "no_results",
            "location": payload.location,
            "keyword": search_keyword,
            "records_processed": 0,
            "records_saved": 0,
            "leads": [],
        }

    # Step 2: Audit each business website
    audited_results: List[tuple[Dict[str, str | None], str]] = []
    for biz in businesses:
        url = biz.get("website")
        status = audit_website(url)
        audited_results.append((biz, status))

    # Step 3: Persist records to Supabase
    saved_count = save_leads(audited_results)

    # Step 4: Format and return response
    formatted_leads = [
        {
            "business_name": biz.get("business_name"),
            "phone_number": biz.get("phone_number"),
            "address": biz.get("address"),
            "website": biz.get("website"),
            "status_flag": status,
        }
        for biz, status in audited_results
    ]

    return {
        "status": "success",
        "location": payload.location,
        "keyword": search_keyword,
        "records_processed": len(formatted_leads),
        "records_saved": saved_count,
        "leads": formatted_leads,
    }


if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)