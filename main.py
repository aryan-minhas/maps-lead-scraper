"""
main.py
=======
End-to-end integration pipeline for the Maps Lead Scraper.

Orchestrates:
    1. scraper.py  – fetches business leads from Google Places (or mock data)
    2. auditor.py  – audits each business website for quality / health
    3. Console     – renders a formatted summary table to stdout
"""

import io
import logging
import sys
import textwrap

# Force UTF-8 output on Windows terminals (cp1252 cannot encode box chars)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from auditor import audit_website    # pyrefly: ignore [missing-import]
from database import save_leads      # pyrefly: ignore [missing-import]
from scraper import fetch_places     # pyrefly: ignore [missing-import]

# ---------------------------------------------------------------------------
# Logging configuration (no-op if already initialised by scraper / auditor)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

# Status flag → coloured label mapping (ANSI escape codes)
_STATUS_LABELS: dict[str, str] = {
    "ACTIVE_WEBSITE":      "\033[92m ACTIVE_WEBSITE      \033[0m",  # green
    "INSECURE_WEBSITE":    "\033[93m INSECURE_WEBSITE    \033[0m",  # yellow
    "NOT_MOBILE_FRIENDLY": "\033[94m NOT_MOBILE_FRIENDLY \033[0m",  # blue
    "BROKEN_WEBSITE":      "\033[91m BROKEN_WEBSITE      \033[0m",  # red
    "NO_WEBSITE":          "\033[90m NO_WEBSITE          \033[0m",  # grey
}

# Column widths for the results table
_COL = {
    "idx":     4,
    "name":    30,
    "phone":   20,
    "address": 38,
    "website": 38,
    "status":  22,
}


def _truncate(text: str | None, width: int) -> str:
    """Return *text* truncated with ellipsis to *width* chars."""
    if not text:
        return "—".ljust(width)
    return textwrap.shorten(str(text), width=width, placeholder="…").ljust(width)


def _separator(char: str = "─") -> str:
    """Build a full-width row separator."""
    total = sum(_COL.values()) + len(_COL) * 3 + 1  # account for │ padding
    return char * total


def _header_row() -> str:
    """Build the column header row."""
    cols = [
        "#".center(_COL["idx"]),
        "Business Name".ljust(_COL["name"]),
        "Phone".ljust(_COL["phone"]),
        "Address".ljust(_COL["address"]),
        "Website".ljust(_COL["website"]),
        "Audit Status".ljust(_COL["status"]),
    ]
    return "│ " + " │ ".join(cols) + " │"


def _data_row(idx: int, biz: dict[str, str | None], status: str) -> str:
    """Build a single data row for one business."""
    label = _STATUS_LABELS.get(status, status.ljust(_COL["status"]))
    cols = [
        str(idx).center(_COL["idx"]),
        _truncate(biz["business_name"], _COL["name"]),
        _truncate(biz["phone_number"],  _COL["phone"]),
        _truncate(biz["address"],       _COL["address"]),
        _truncate(biz["website"],       _COL["website"]),
        label,
    ]
    return "│ " + " │ ".join(cols) + " │"


def _print_table(results: list[tuple[dict[str, str | None], str]]) -> None:
    """Render the full results table to stdout."""
    sep      = _separator("─")
    thick    = _separator("═")
    thin_sep = _separator("┄")

    print()
    print(thick)
    print("  MAPS LEAD SCRAPER -- WEBSITE AUDIT RESULTS")
    print(thick)
    print(_header_row())
    print(sep)

    for idx, (biz, status) in enumerate(results, start=1):
        print(_data_row(idx, biz, status))
        if idx < len(results):
            print(thin_sep)

    print(sep)

    # ── Summary footer ──────────────────────────────────────────────────
    counts: dict[str, int] = {}
    for _, status in results:
        counts[status] = counts.get(status, 0) + 1

    print(f"\n  Summary  ({len(results)} business(es) audited)")
    print(f"  {'─' * 38}")
    for flag, count in sorted(counts.items(), key=lambda x: x[0]):
        bar = "█" * count
        print(f"  {flag:<22}  {bar}  ({count})")
    print()


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the end-to-end scrape → audit → report pipeline."""
    location = "Miami, FL"
    keyword  = "plumber"

    logger.info("Pipeline started — location=%r  keyword=%r", location, keyword)

    # ── Step 1: Fetch business leads ────────────────────────────────────
    businesses = fetch_places(location, keyword)

    if not businesses:
        logger.warning("No businesses returned. Exiting.")
        print("\n⚠️  No results to display.\n")
        return

    logger.info("Fetched %d business(es). Starting website audits…", len(businesses))

    # ── Step 2: Audit each website ──────────────────────────────────────
    results: list[tuple[dict[str, str | None], str]] = []

    for biz in businesses:
        website_url = biz.get("website")
        logger.info(
            "Auditing %-30s → %s",
            biz.get("business_name", "?"),
            website_url or "None",
        )
        status = audit_website(website_url)
        results.append((biz, status))

    # ── Step 3: Persist results to Supabase ────────────────────────────
    saved_count = save_leads(results)
    logger.info(
        "Database: %d record(s) saved/updated in Supabase.", saved_count
    )

    # ── Step 4: Print formatted table ──────────────────────────────────
    _print_table(results)

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
