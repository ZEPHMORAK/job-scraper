"""
scrapers/real_estate.py — Real estate lead discovery
"""
import hashlib
import time
import config
from core.ddg_search import ddg_search, make_session
from core.email_extractor import extract_email_from_text, extract_email_from_url


def scrape_real_estate(cities: list = None, max_per_city: int = 5) -> list[dict]:
    cities = cities or config.REAL_ESTATE_CITIES
    leads = []
    seen = set()
    session = make_session()

    for city in cities:
        query = f"real estate agency {city} contact email website"
        print(f"[RealEstate] Searching: {query}")
        results = ddg_search(session, query, max_per_city + 2)

        count = 0
        for r in results:
            if count >= max_per_city:
                break
            url = r["url"]
            if not url or url in seen:
                continue
            if any(s in url for s in ["linkedin.com", "facebook.com", "twitter.com"]):
                continue
            seen.add(url)

            email = extract_email_from_text(r["snippet"])
            if not email:
                email = extract_email_from_url(url)

            lead_id = "re_" + hashlib.md5(url.encode()).hexdigest()[:12]
            leads.append({
                "id": lead_id,
                "platform": "real_estate",
                "type": "lead",
                "niche": "real_estate",
                "title": r["title"][:100],
                "description": f"Real estate in {city}. {r['snippet'][:200]}",
                "url": url,
                "linkedin": "",
                "company": city,
                "location": city,
                "email": email or "",
                "phone": "",
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "score": 0,
            })
            count += 1
            print(f"[RealEstate] Found: {r['title'][:60]} | email: {email or 'none'}")

        time.sleep(2)

    print(f"[RealEstate] Total leads: {len(leads)}")
    return leads
