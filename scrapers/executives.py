"""
scrapers/executives.py — Executive lead discovery (CEOs, founders, MDs)
"""
import hashlib
import time
from core.ddg_search import ddg_search, make_session

QUERIES = [
    "CEO founder Nigeria company website contact email",
    "managing director consulting Lagos Nigeria contact",
    "founder technology startup Nigeria email",
    "CEO real estate company Lagos contact",
    "managing director law firm Nigeria website",
    "founder coaching business Nigeria contact email",
    "chief executive officer Nigeria company website",
    "director consulting Abuja Nigeria email",
]


def scrape_executives(max_per_query: int = 6) -> list[dict]:
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
        time.sleep(1.5)

    print(f"[Executives] {len(leads)} leads found")
    return leads
