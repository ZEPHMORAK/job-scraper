"""
scrapers/executives.py — Executive lead discovery (CEOs, founders, MDs)
Uses DuckDuckGo HTML scraping
"""
import hashlib
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
    '"CEO" "founder" Nigeria startup automation contact',
    '"managing director" consulting firm Lagos email website',
    '"founder" technology company Nigeria contact',
    '"CEO" real estate Lagos Nigeria website',
    '"managing director" law firm Nigeria contact email',
    '"founder" coaching business Lagos email',
    '"chief executive" company Nigeria website contact',
    '"director" consulting firm Abuja email website',
]


def _ddg_search(session, query: str, max_results: int = 6) -> list[dict]:
    results = []
    try:
        resp = session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
            verify=False,
        )
        if resp.status_code != 200:
            print(f"[Executives] DDG returned {resp.status_code} for: {query[:40]}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for r in soup.select("a.result__a")[:max_results]:
            url = r.get("href", "")
            title = r.get_text(strip=True)
            snippet = ""
            parent = r.find_parent("div", class_="result")
            if parent:
                s = parent.select_one(".result__snippet")
                if s:
                    snippet = s.get_text(strip=True)
            if url:
                results.append({"url": url, "title": title, "snippet": snippet})
    except Exception as e:
        print(f"[Executives] Search error: {e}")
    return results


def scrape_executives(max_per_query: int = 6) -> list[dict]:
    leads = []
    seen = set()
    session = requests.Session()
    try:
        session.get("https://duckduckgo.com/", headers=HEADERS, timeout=10, verify=False)
    except Exception:
        pass

    for query in QUERIES:
        results = _ddg_search(session, query, max_per_query)
        for r in results:
            url = r["url"]
            if url in seen:
                continue
            seen.add(url)
            lead_id = "exec_" + hashlib.md5(url.encode()).hexdigest()[:12]
            linkedin = url if "linkedin.com" in url else ""

            leads.append({
                "id": lead_id,
                "platform": "executive",
                "type": "lead",
                "niche": "executive",
                "title": r["title"],
                "description": r["snippet"],
                "url": url,
                "linkedin": linkedin,
                "company": "",
                "location": "Nigeria",
                "email": "",
                "phone": "",
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "score": 0,
            })
        time.sleep(1.2)

    print(f"[Executives] {len(leads)} leads found")
    return leads
