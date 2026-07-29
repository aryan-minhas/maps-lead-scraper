"""
test_auditor.py
---------------
Mock test suite for auditor.py.
Verifies website auditing logic against various mock URL edge cases
without relying on external live scraper feeds.
"""

import unittest
from unittest.mock import MagicMock, patch

# Import auditor functions
from auditor import audit_website


class TestAuditor(unittest.TestCase):

    def test_no_website(self):
        """Test missing, None, or empty website URLs."""
        self.assertEqual(audit_website(None), "NO_WEBSITE")
        self.assertEqual(audit_website(""), "NO_WEBSITE")
        self.assertEqual(audit_website("   "), "NO_WEBSITE")

    @patch("requests.get")
    def test_active_website(self, mock_get):
        """Test a normal, secure, mobile-friendly website (200 OK)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><head><meta name="viewport" content="width=device-width"></head></html>'
        mock_get.return_value = mock_response

        status = audit_website("https://example.com")
        self.assertEqual(status, "ACTIVE_WEBSITE")

    @patch("requests.get")
    def test_insecure_website(self, mock_get):
        """Test HTTP URL without SSL or insecure fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><head><meta name="viewport" content="width=device-width"></head></html>'
        mock_get.return_value = mock_response

        status = audit_website("http://example.com")
        self.assertEqual(status, "INSECURE_WEBSITE")

    @patch("requests.get")
    def test_broken_website_404(self, mock_get):
        """Test HTTP 404 or 500 error pages."""
        import requests
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "404 Not Found"
        
        # Create an HTTPError and attach the mock response object to it
        http_err = requests.exceptions.HTTPError("404 Client Error")
        http_err.response = mock_response
        
        mock_response.raise_for_status.side_effect = http_err
        mock_get.return_value = mock_response

        status = audit_website("https://example.com/broken")
        self.assertEqual(status, "BROKEN_WEBSITE")

    @patch("requests.get")
    def test_broken_website_connection_error(self, mock_get):
        """Test DNS failure, timeout, or unreachable connection."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection timed out")

        status = audit_website("https://nonexistent-domain-xyz123.com")
        self.assertEqual(status, "BROKEN_WEBSITE")

    @patch("requests.get")
    def test_not_mobile_friendly(self, mock_get):
        """Test website missing viewport meta tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><head></head><body>Desktop layout</body></html>'
        mock_get.return_value = mock_response

        status = audit_website("https://desktop-only.com")
        self.assertEqual(status, "NOT_MOBILE_FRIENDLY")


if __name__ == "__main__":
    unittest.main()