"""
scrapers/academic.py — Academic researcher lead discovery
Targets PhD students, professors, research fellows on .edu / .ac.uk sites
"""
import re
import hashlib
import time
import config
from core.ddg_search import ddg_search, make_session
from core.email_extractor import extract_email_from_text, extract_email_from_url

ACADEMIC_DOMAINS = [".edu", ".ac.uk", ".ac.ng", ".ac.za"]


def _extract_university(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if m:
        domain = m.group(1)
        parts = domain.split(".")
        if "edu" in parts:
            idx = parts.index("edu")
            return ".".join(parts[max(0, idx - 1):idx + 1])
        return domain
    return ""


def scrape_academic(queries: list = None, max_per_query: int = 5) -> list[dict]:
    queries = queries or config.ACADEMIC_QUERIES
    leads = []
    seen = set()
    session = make_session()

    for query in queries:
        print(f"[Academic] Searching: {query}")
        results = ddg_search(session, query, max_per_query + 3)

        count = 0
        for r in results:
            if count >= max_per_query:
                break
            url = r["url"]
            if not url or url in seen:
                continue
            if not any(d in url for d in ACADEMIC_DOMAINS):
                continue
            seen.add(url)

            email = extract_email_from_text(r["snippet"])
            if not email:
                email = extract_email_from_url(url)

            university = _extract_university(url)
            lead_id = "acad_" + hashlib.md5(url.encode()).hexdigest()[:12]

            leads.append({
                "id": lead_id,
                "platform": "academic",
                "type": "lead",
                "niche": "academic",
                "title": r["title"][:100],
                "description": f"Academic researcher. {r['snippet'][:200]}",
                "url": url,
                "linkedin": "",
                "company": university,
                "location": university,
                "email": email or "",
                "phone": "",
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "score": 0,
            })
            count += 1
            print(f"[Academic] Found: {r['title'][:60]} | {university} | email: {email or 'none'}")

        time.sleep(2)

    print(f"[Academic] Total leads: {len(leads)}")
    return leads
