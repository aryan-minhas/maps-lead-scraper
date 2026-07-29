"""
auditor.py
==========
Performs a structured quality audit on a business website URL.

Audit hierarchy (evaluated in strict order):
    1. NO_WEBSITE         – URL is None, empty, or "N/A"
    2. BROKEN_WEBSITE     – Network error, timeout, or HTTP 4xx/5xx
    3. INSECURE_WEBSITE   – URL uses plain http:// instead of https://
    4. NOT_MOBILE_FRIENDLY – Missing <meta name="viewport"> tag
    5. ACTIVE_WEBSITE     – Passes all checks

Each check is only reached if all prior checks passed, ensuring the
returned status string is always the most severe applicable finding.
"""

import logging

import requests
from bs4 import BeautifulSoup # pyrefly: ignore [missing-import]

# ---------------------------------------------------------------------------
# Logging configuration
# Note: If scraper.py has already called basicConfig, this is a no-op.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_REQUEST_TIMEOUT: int = 5  # seconds

_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

_HEADERS: dict[str, str] = {
    "User-Agent": _USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Status flag constants
# ---------------------------------------------------------------------------
STATUS_NO_WEBSITE: str = "NO_WEBSITE"
STATUS_BROKEN: str = "BROKEN_WEBSITE"
STATUS_INSECURE: str = "INSECURE_WEBSITE"
STATUS_NOT_MOBILE: str = "NOT_MOBILE_FRIENDLY"
STATUS_ACTIVE: str = "ACTIVE_WEBSITE"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_website(url: str | None) -> str:
    """
    Run a structured quality audit on a business website URL.

    The checks are applied in strict priority order. The first failing
    check determines the returned status; subsequent checks are skipped.

    Parameters
    ----------
    url : The website URL string to audit, or ``None``.

    Returns
    -------
    One of the following status strings:

    ``"NO_WEBSITE"``
        The URL is ``None``, empty, or equal to ``"N/A"``.

    ``"BROKEN_WEBSITE"``
        A ``ConnectionError``, ``Timeout``, or an HTTP 4xx/5xx response
        was received.

    ``"INSECURE_WEBSITE"``
        The URL uses ``http://`` instead of ``https://``.

    ``"NOT_MOBILE_FRIENDLY"``
        The HTML page is missing a ``<meta name="viewport">`` tag.

    ``"ACTIVE_WEBSITE"``
        The URL passed every check above.

    Notes
    -----
    This function will **never** raise an exception. All network and
    parsing errors are caught internally and mapped to the appropriate
    status flag so that a single bad URL never aborts the pipeline loop.
    """

    # ------------------------------------------------------------------
    # CHECK 1: Presence guard
    # ------------------------------------------------------------------
    if not url or url.strip() in {"", "N/A"}:
        logger.info("Audit [NO_WEBSITE] – URL is absent or N/A: %r", url)
        return STATUS_NO_WEBSITE

    url = url.strip()

    # ------------------------------------------------------------------
    # CHECK 2: HTTP connectivity & status code
    # ------------------------------------------------------------------
    response: requests.Response | None = None

    try:
        response = requests.get(
            url,
            headers=_HEADERS,
            timeout=_REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        # Raises HTTPError for 4xx / 5xx status codes
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        logger.warning(
            "Audit [BROKEN_WEBSITE] – Connection refused or DNS failure: %s", url
        )
        return STATUS_BROKEN

    except requests.exceptions.Timeout:
        logger.warning(
            "Audit [BROKEN_WEBSITE] – Request timed out after %ds: %s",
            _REQUEST_TIMEOUT,
            url,
        )
        return STATUS_BROKEN

    except requests.exceptions.HTTPError as exc:
        logger.warning(
            "Audit [BROKEN_WEBSITE] – HTTP %s received for: %s",
            exc.response.status_code,
            url,
        )
        return STATUS_BROKEN

    except requests.exceptions.TooManyRedirects:
        logger.warning(
            "Audit [BROKEN_WEBSITE] – Too many redirects for: %s", url
        )
        return STATUS_BROKEN

    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Audit [BROKEN_WEBSITE] – Unexpected network error for %s: %s", url, exc
        )
        return STATUS_BROKEN

    # ------------------------------------------------------------------
    # CHECK 3: Security (HTTPS enforcement)
    # Evaluated against the *original* URL, not the post-redirect URL,
    # so that insecure starting points are still flagged even if the
    # server ultimately redirects to HTTPS.
    # ------------------------------------------------------------------
    if url.lower().startswith("http://"):
        logger.info("Audit [INSECURE_WEBSITE] – Plain HTTP URL: %s", url)
        return STATUS_INSECURE

    # ------------------------------------------------------------------
    # CHECK 4: Mobile optimisation (viewport meta tag)
    # ------------------------------------------------------------------
    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Match <meta name="viewport"> (case-insensitive attribute value)
        viewport_tag = soup.find(
            "meta",
            attrs={"name": lambda val: val and val.lower() == "viewport"},
        )

        if viewport_tag is None:
            logger.info(
                "Audit [NOT_MOBILE_FRIENDLY] – No viewport meta tag found: %s", url
            )
            return STATUS_NOT_MOBILE

    except Exception as exc:  # noqa: BLE001 – intentionally broad for HTML parsing
        logger.warning(
            "Audit [NOT_MOBILE_FRIENDLY] – HTML parse error for %s: %s", url, exc
        )
        return STATUS_NOT_MOBILE

    # ------------------------------------------------------------------
    # CHECK 5: All checks passed
    # ------------------------------------------------------------------
    logger.info("Audit [ACTIVE_WEBSITE] – %s", url)
    return STATUS_ACTIVE
