"""
scraper.py
==========
Fetches business leads from the Google Places Text Search API.

If no valid API key is found, a mock data fallback is used so the
pipeline can be exercised end-to-end without a live credential.
"""

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv # pyrefly: ignore [missing-import]

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env file (safe to call even if the file does not exist)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

_SENTINEL_KEYS = {"", "YOUR_API_KEY_HERE"}

# ---------------------------------------------------------------------------
# Mock data – used when no valid API key is present
# ---------------------------------------------------------------------------
MOCK_BUSINESSES: list[dict[str, str | None]] = [
    {
        "business_name": "Miami Plumbing Pros",
        "phone_number": "+1-305-555-0101",
        "address": "123 Brickell Ave, Miami, FL 33131",
        "website": "https://miamiplumbingpros.com",
    },
    {
        "business_name": "South Florida Pipe Masters",
        "phone_number": "+1-305-555-0182",
        "address": "456 Coral Way, Miami, FL 33145",
        "website": "http://sfpipemasters.com",  # intentionally http for audit demo
    },
    {
        "business_name": "24/7 Emergency Plumbers Miami",
        "phone_number": "+1-786-555-0234",
        "address": "789 NW 7th St, Miami, FL 33126",
        "website": None,  # no website – for audit demo
    },
    {
        "business_name": "Bayfront Drain & Rooter",
        "phone_number": "+1-305-555-0317",
        "address": "321 Bayshore Dr, Miami, FL 33137",
        "website": "https://bayfrontdrainrooter.com",
    },
    {
        "business_name": "Liberty City Plumbing Co.",
        "phone_number": "+1-305-555-0445",
        "address": "890 NW 54th St, Miami, FL 33142",
        "website": "https://libertycityplumbing.com",
    },
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_place_result(place: dict[str, Any], api_key: str) -> dict[str, str | None]:
    """
    Convert a raw Places API result dict into the canonical business dict.

    A secondary Details API call is made to retrieve the phone number and
    website URL, which are not included in Text Search results.

    Parameters
    ----------
    place   : A single element from the `results` array returned by the
              Text Search endpoint.
    api_key : The validated Google Places API key.

    Returns
    -------
    A dict matching the schema:
        business_name, phone_number, address, website
    """
    place_id: str = place.get("place_id", "")
    name: str = place.get("name", "N/A")
    address: str = place.get("formatted_address", "N/A")

    phone_number: str = "N/A"
    website: str | None = None

    if place_id:
        try:
            details_resp = requests.get(
                PLACE_DETAILS_URL,
                params={
                    "place_id": place_id,
                    "fields": "formatted_phone_number,website",
                    "key": api_key,
                },
                timeout=10,
            )
            details_resp.raise_for_status()
            details: dict[str, Any] = details_resp.json().get("result", {})
            phone_number = details.get("formatted_phone_number", "N/A")
            website = details.get("website")  # None if key absent
        except requests.exceptions.Timeout:
            logger.warning(
                "Timeout fetching details for place_id=%s (%s). Skipping details.",
                place_id,
                name,
            )
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Connection error fetching details for place_id=%s (%s).",
                place_id,
                name,
            )
        except requests.exceptions.HTTPError as exc:
            logger.warning(
                "HTTP error %s fetching details for place_id=%s (%s).",
                exc.response.status_code,
                place_id,
                name,
            )
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Unexpected request error fetching details for %s: %s",
                name,
                exc,
            )

    return {
        "business_name": name,
        "phone_number": phone_number,
        "address": address,
        "website": website,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_places(location: str, keyword: str) -> list[dict[str, str | None]]:
    """
    Search Google Places for businesses matching *keyword* near *location*.

    Parameters
    ----------
    location : Human-readable location string, e.g. ``"Miami, FL"``.
    keyword  : Business category or search term, e.g. ``"plumber"``.

    Returns
    -------
    A list of dicts, each containing:
        - ``business_name`` (str)
        - ``phone_number``  (str)
        - ``address``       (str)
        - ``website``       (str | None)

    Raises
    ------
    This function will **not** propagate exceptions; all errors are caught,
    logged, and handled by returning an empty list or the mock dataset.
    """
    api_key: str | None = os.getenv("GOOGLE_PLACES_API_KEY")

    # ------------------------------------------------------------------
    # Guard: missing or placeholder API key → use mock data
    # ------------------------------------------------------------------
    if not api_key or api_key.strip() in _SENTINEL_KEYS:
        logger.warning(
            "GOOGLE_PLACES_API_KEY is missing or set to a placeholder value. "
            "Falling back to MOCK DATA for testing purposes."
        )
        return MOCK_BUSINESSES

    query = f"{keyword} in {location}"
    logger.info("Querying Google Places API: %r", query)

    businesses: list[dict[str, str | None]] = []

    try:
        response = requests.get(
            PLACES_API_URL,
            params={"query": query, "key": api_key},
            timeout=10,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        api_status: str = data.get("status", "UNKNOWN")

        if api_status != "OK":
            logger.error(
                "Google Places API returned non-OK status: %s. "
                "Check your API key and quota. Returning empty list.",
                api_status,
            )
            return []

        places: list[dict[str, Any]] = data.get("results", [])
        logger.info("Found %d place(s) for query %r.", len(places), query)

        for place in places:
            business = _build_place_result(place, api_key)
            businesses.append(business)

    except requests.exceptions.Timeout:
        logger.error(
            "Request timed out while contacting Google Places API for query %r.",
            query,
        )
    except requests.exceptions.ConnectionError:
        logger.error(
            "Could not connect to Google Places API. "
            "Check your internet connection. Query was: %r",
            query,
        )
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "HTTP error %s from Google Places API for query %r.",
            exc.response.status_code,
            query,
        )
    except requests.exceptions.RequestException as exc:
        logger.error(
            "An unexpected request error occurred for query %r: %s",
            query,
            exc,
        )
    except (KeyError, ValueError) as exc:
        logger.error(
            "Failed to parse Google Places API response for query %r: %s",
            query,
            exc,
        )

    return businesses
