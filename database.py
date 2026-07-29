"""
database.py
-----------
Handles all database interactions with Supabase for the maps-lead-scraper
pipeline.  If valid credentials are not found in the environment, the module
falls back to a MOCK/LOGGING mode so the rest of the application can still
run without a live database connection.
"""

import logging
import os
from typing import Any

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------
load_dotenv()

_SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# Placeholder strings that indicate the user has not yet filled in real values.
_PLACEHOLDER_STRINGS: set[str] = {
    "",
    "YOUR_SUPABASE_URL_HERE",
    "YOUR_SUPABASE_KEY_HERE",
}

_MOCK_MODE: bool = False
_supabase_client = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

def _init_client() -> None:
    """Initialise the Supabase client, or activate MOCK mode on failure."""
    global _supabase_client, _MOCK_MODE

    if _SUPABASE_URL in _PLACEHOLDER_STRINGS or _SUPABASE_KEY in _PLACEHOLDER_STRINGS:
        logger.warning(
            "Supabase credentials are missing or set to placeholder values. "
            "Running in MOCK/LOGGING mode — all database operations will be "
            "logged to the console instead of executed against a real database."
        )
        _MOCK_MODE = True
        return

    try:
        # pyrefly: ignore [missing-import]
        from supabase import Client, create_client  # noqa: PLC0415

        _supabase_client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
        logger.info("Supabase client initialised successfully.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to initialise Supabase client (%s). "
            "Falling back to MOCK/LOGGING mode.",
            exc,
        )
        _MOCK_MODE = True


# Run once at import time.
_init_client()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_leads(leads_data: list[tuple[dict[str, str | None], str]]) -> int:
    """Upsert a batch of business leads into the Supabase ``leads`` table.

    Parameters
    ----------
    leads_data:
        A list of ``(business_dict, status_flag)`` tuples where
        ``business_dict`` contains the keys ``business_name``, ``phone_number``,
        ``address``, and ``website``.

    Returns
    -------
    int
        The number of records successfully saved/upserted.
    """
    if not leads_data:
        logger.debug("save_leads called with an empty list — nothing to do.")
        return 0

    # Build the payload expected by the Supabase table schema.
    records: list[dict[str, str | None]] = []
    for biz, status_flag in leads_data:
        records.append(
            {
                "business_name": biz.get("business_name"),
                "phone_number": biz.get("phone_number"),
                "address": biz.get("address"),
                "website": biz.get("website"),
                "status_flag": status_flag,
            }
        )

    if _MOCK_MODE:
        logger.info(
            "[MOCK] save_leads — would upsert %d record(s):", len(records)
        )
        for record in records:
            logger.info("  [MOCK]   %s", record)
        return len(records)

    try:
        response = (
            _supabase_client.table("leads")
            .upsert(records, on_conflict="business_name,address")
            .execute()
        )
        saved_count: int = len(response.data) if response.data else 0
        logger.info("save_leads — upserted %d record(s) successfully.", saved_count)
        return saved_count
    except Exception as exc:  # noqa: BLE001
        logger.error("save_leads — database error during upsert: %s", exc)
        return 0


def get_all_leads() -> list[dict[str, Any]]:
    """Retrieve all rows from the ``leads`` table, newest first.

    Returns
    -------
    list[dict[str, Any]]
        A list of row dictionaries ordered by ``created_at`` descending.
        Returns an empty list on error or in MOCK mode.
    """
    if _MOCK_MODE:
        logger.info(
            "[MOCK] get_all_leads — would query all rows from 'leads' "
            "ordered by created_at DESC."
        )
        return []

    try:
        response = (
            _supabase_client.table("leads")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        leads: list[dict[str, Any]] = response.data if response.data else []
        logger.info("get_all_leads — retrieved %d row(s).", len(leads))
        return leads
    except Exception as exc:  # noqa: BLE001
        logger.error("get_all_leads — database error during query: %s", exc)
        return []
