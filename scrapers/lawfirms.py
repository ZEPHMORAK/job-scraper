"""
scrapers/lawfirms.py — Law firm lead discovery
"""
import hashlib
import time
from core.ddg_search import ddg_search, make_session

QUERIES = [
    "law firm Lagos Nigeria website contact email",
    "legal services attorney Nigeria contact website",
    "law partners Abuja Nigeria email website",
    "solicitor Lagos Nigeria website email",
    "legal practice Nigeria email website",
    "law chambers Lagos Nigeria website contact",
    "barrister attorney Nigeria contact email",
    "corporate law firm Nigeria website",
]


def scrape_lawfirms(max_per_query: int = 6) -> list[dict]:
    leads = []
    seen = set()
    session = make_session()

    for query in QUERIES:
        results = ddg_search(session, query, max_per_query)
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
        time.sleep(1.5)

    print(f"[LawFirms] {len(leads)} leads found")
    return leads
