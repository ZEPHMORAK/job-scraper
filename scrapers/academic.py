"""
scrapers/academic.py — Scrape academic researcher leads via DuckDuckGo.
Targets PhD students, professors, and research fellows on .edu sites.
No paid API required.
"""
import re
import time
import random
import hashlib
import requests
import urllib3
from bs4 import BeautifulSoup
from core.email_extractor import extract_email_from_url, extract_email_from_text
import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

DDG_URL = "https://html.duckduckgo.com/html/"


def _search_ddg(query: str, max_results: int = 8) -> list[dict]:
    """Search DuckDuckGo HTML and return list of {title, url, snippet}."""
    for attempt in range(3):
        try:
            session = requests.Session()
            session.verify = False
            session.get("https://duckduckgo.com/", headers=HEADERS, timeout=10)
            time.sleep(random.uniform(1.5, 2.5))
            resp = session.post(
                DDG_URL,
                data={"q": query, "b": "", "kl": "us-en"},
                headers={**HEADERS, "Referer": "https://duckduckgo.com/"},
                timeout=20,
            )
            if resp.status_code != 200:
                if attempt < 2:
                    time.sleep(random.uniform(3.0, 6.0))
                    continue
                print(f"[Academic] DDG returned {resp.status_code} for: {query}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for r in soup.select(".result__body")[:max_results]:
                title_el = r.select_one("a.result__a")
                snippet_el = r.select_one(".result__snippet")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                if url and url.startswith("http"):
                    results.append({"title": title, "url": url, "snippet": snippet})
            return results
        except Exception as e:
            if attempt < 2:
                time.sleep(random.uniform(2.0, 4.0))
            else:
                print(f"[Academic] Search error: {e}")
    return []


def _extract_university(url: str) -> str:
    """Extract university domain from URL."""
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if m:
        domain = m.group(1)
        # Return just the .edu domain part
        parts = domain.split(".")
        if "edu" in parts:
            idx = parts.index("edu")
            return ".".join(parts[max(0, idx - 1):idx + 1])
        return domain
    return ""


def scrape_academic(queries: list[str] = None, max_per_query: int = 5) -> list[dict]:
    """
    Search for academic researchers using .edu site queries.
    Returns normalized lead dicts.
    """
    queries = queries or config.ACADEMIC_QUERIES
    all_leads = []
    seen_urls = set()

    for query in queries:
        print(f"[Academic] Searching: {query}")
        results = _search_ddg(query, max_results=max_per_query + 3)

        count = 0
        for r in results:
            if count >= max_per_query:
                break
            url = r["url"]
            if not url or url in seen_urls:
                continue

            # Only accept .edu and known academic domains
            if not any(d in url for d in [".edu", ".ac.uk", ".ac.ng", "research.", "scholar."]):
                continue

            seen_urls.add(url)

            # Extract email from snippet first, then page
            email = extract_email_from_text(r["snippet"])
            if not email:
                time.sleep(random.uniform(1.0, 2.5))
                email = extract_email_from_url(url)

            university = _extract_university(url)
            lead_id = "acad-" + hashlib.md5(url.encode()).hexdigest()[:12]

            lead = {
                "id": lead_id,
                "platform": "academic",
                "title": r["title"][:100],
                "company": university,
                "url": url,
                "email": email,
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "description": f"Academic researcher. {r['snippet'][:200]}",
                "posted_at": "",
                "niche": "academic",
                "type": "lead",
            }
            all_leads.append(lead)
            count += 1
            print(f"[Academic] Found: {r['title'][:60]} | {university} | email: {email or 'none'}")

        time.sleep(random.uniform(3.0, 6.0))

    print(f"[Academic] Total leads: {len(all_leads)}")
    return all_leads
