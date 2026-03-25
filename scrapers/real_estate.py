"""
scrapers/real_estate.py — Scrape real estate agent leads via DuckDuckGo HTML search.
No API key required. Extracts name, website, title per city.
"""
import re
import time
import random
import hashlib
import requests
from bs4 import BeautifulSoup
from core.email_extractor import extract_email_from_url, extract_email_from_text
import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

DDG_URL = "https://html.duckduckgo.com/html/"


def _search_ddg(query: str, max_results: int = 8) -> list[dict]:
    """Search DuckDuckGo HTML and return list of {title, url, snippet}."""
    try:
        resp = requests.post(
            DDG_URL,
            data={"q": query, "b": "", "kl": "us-en"},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"[RealEstate] DDG returned {resp.status_code} for: {query}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result__body")[:max_results]:
            title_el = r.select_one(".result__title a")
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
        print(f"[RealEstate] Search error: {e}")
        return []


def scrape_real_estate(cities: list[str] = None, max_per_city: int = 5) -> list[dict]:
    """
    Search for real estate agents in each city.
    Returns normalized lead dicts.
    """
    cities = cities or config.REAL_ESTATE_CITIES
    all_leads = []
    seen_urls = set()

    for city in cities:
        query = f'real estate agent {city} contact email'
        print(f"[RealEstate] Searching: {query}")
        results = _search_ddg(query, max_results=max_per_city + 3)

        count = 0
        for r in results:
            if count >= max_per_city:
                break
            url = r["url"]
            if not url or url in seen_urls:
                continue

            # Skip social media, directories with no individual contact pages
            if any(skip in url for skip in ["linkedin.com", "facebook.com", "twitter.com",
                                             "zillow.com/profile", "realtor.com/realestateagents"]):
                continue

            seen_urls.add(url)

            # Try to extract email from snippet first (faster), then from page
            email = extract_email_from_text(r["snippet"])
            if not email:
                time.sleep(random.uniform(1.0, 2.5))
                email = extract_email_from_url(url)

            lead_id = "re-" + hashlib.md5(url.encode()).hexdigest()[:12]
            lead = {
                "id": lead_id,
                "platform": "real_estate",
                "title": r["title"][:100],
                "company": city,
                "url": url,
                "email": email,
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "description": f"Real estate agent in {city}. {r['snippet'][:200]}",
                "posted_at": "",
                "niche": "real estate",
                "type": "lead",
            }
            all_leads.append(lead)
            count += 1
            print(f"[RealEstate] Found: {r['title'][:60]} | email: {email or 'none'}")

        time.sleep(random.uniform(3.0, 5.0))  # be polite between cities

    print(f"[RealEstate] Total leads: {len(all_leads)}")
    return all_leads
