"""
scrapers/lawfirms.py — Law firm lead discovery
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
    '"law firm" Lagos Nigeria contact email website',
    '"legal services" Nigeria attorney website contact',
    '"law partners" Abuja Nigeria contact email',
    '"solicitor" Lagos Nigeria website email',
    '"legal practice" Nigeria email contact website',
    '"law chambers" Lagos Nigeria website',
    '"attorney" Nigeria contact email law firm',
    '"barrister" Lagos Nigeria contact',
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
            print(f"[LawFirms] DDG returned {resp.status_code} for: {query[:40]}")
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
        print(f"[LawFirms] Search error: {e}")
    return results


def scrape_lawfirms(max_per_query: int = 6) -> list[dict]:
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
            lead_id = "law_" + hashlib.md5(url.encode()).hexdigest()[:12]
            linkedin = url if "linkedin.com" in url else ""

            leads.append({
                "id": lead_id,
                "platform": "lawfirm",
                "type": "lead",
                "niche": "law_firm",
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

    print(f"[LawFirms] {len(leads)} leads found")
    return leads
