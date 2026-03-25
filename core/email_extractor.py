"""
core/email_extractor.py — Extract emails from web pages using regex.
No paid APIs. Pure requests + regex.
"""
import re
import time
import random
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Emails to ignore — generic/noreply addresses
IGNORE_PATTERNS = [
    "noreply", "no-reply", "donotreply", "example.com",
    "sentry", "wixpress", "wordpress", "w3.org",
    "schema.org", "cloudflare", "google.com",
    "facebook.com", "twitter.com", "instagram.com",
]

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)


def _is_valid(email: str) -> bool:
    email = email.lower()
    if any(p in email for p in IGNORE_PATTERNS):
        return False
    # Skip image/file extensions accidentally captured
    if re.search(r"\.(png|jpg|gif|svg|css|js)$", email):
        return False
    return True


def extract_email_from_url(url: str, timeout: int = 8) -> str:
    """
    Download a page and return the first real email found.
    Returns empty string if none found or page unreachable.
    """
    if not url or not url.startswith("http"):
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return ""
        emails = EMAIL_REGEX.findall(resp.text)
        for email in emails:
            if _is_valid(email):
                return email.lower()
    except Exception:
        pass
    return ""


def extract_email_from_text(text: str) -> str:
    """Extract first valid email from a raw text/HTML string."""
    emails = EMAIL_REGEX.findall(text)
    for email in emails:
        if _is_valid(email):
            return email.lower()
    return ""
