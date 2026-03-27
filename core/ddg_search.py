"""
core/ddg_search.py — DuckDuckGo search via the Lite endpoint (less bot-protected)
Falls back to the standard HTML endpoint if lite fails.
"""
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "DNT": "1",
}


def ddg_search(session: requests.Session, query: str, max_results: int = 6) -> list[dict]:
    """
    Search DuckDuckGo Lite. Returns list of {title, url, snippet}.
    Automatically retries with standard endpoint on failure.
    """
    results = _lite_search(session, query, max_results)
    if not results:
        time.sleep(1.5)
        results = _html_search(session, query, max_results)
    return results


def make_session() -> requests.Session:
    """Create a session pre-warmed with DuckDuckGo cookies."""
    session = requests.Session()
    try:
        session.get(
            "https://lite.duckduckgo.com/lite/",
            headers=HEADERS,
            timeout=10,
            verify=False,
        )
    except Exception:
        pass
    return session


def _lite_search(session: requests.Session, query: str, max_results: int) -> list[dict]:
    """Search via lite.duckduckgo.com (GET request, simpler bot detection)."""
    try:
        resp = session.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query, "kl": "us-en"},
            headers=HEADERS,
            timeout=20,
            verify=False,
        )
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        # DDG Lite HTML structure: results in <table> rows
        # Links: <a class="result-link"> or just <a> inside result rows
        links = soup.select("a.result-link") or soup.select("tr td a[href^='http']")

        for a in links[:max_results]:
            url = a.get("href", "")
            if not url or not url.startswith("http"):
                continue
            title = a.get_text(strip=True)

            # Snippet is usually in the next sibling row
            snippet = ""
            tr = a.find_parent("tr")
            if tr and tr.find_next_sibling("tr"):
                snippet = tr.find_next_sibling("tr").get_text(strip=True)

            results.append({"url": url, "title": title or url, "snippet": snippet})

        return results
    except Exception as e:
        return []


def _html_search(session: requests.Session, query: str, max_results: int) -> list[dict]:
    """Fallback: search via html.duckduckgo.com (POST request)."""
    try:
        resp = session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "us-en"},
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
            verify=False,
        )
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a in soup.select("a.result__a")[:max_results]:
            url = a.get("href", "")
            if not url:
                continue
            title = a.get_text(strip=True)
            snippet = ""
            parent = a.find_parent("div", class_="result")
            if parent:
                s = parent.select_one(".result__snippet")
                if s:
                    snippet = s.get_text(strip=True)
            results.append({"url": url, "title": title or url, "snippet": snippet})

        return results
    except Exception:
        return []
