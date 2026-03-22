"""
scrapers/linkedin.py — Scrape LinkedIn jobs via undocumented guest API.
Returns HTML fragments parsed with BeautifulSoup.
No login required. Uses random User-Agents + delays to reduce block risk.
"""
import re
import time
import random
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import config

GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def _get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.linkedin.com/jobs/search/",
        "Cache-Control": "no-cache",
    }


def _extract_job_id(url: str) -> str | None:
    m = re.search(r"/view/(\d+)/", url)
    return m.group(1) if m else None


def _is_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(kw in lowered for kw in ["authwall", "sign-in", "join now", "linkedin login"])


def scrape_linkedin(keywords: list[str] = None, location: str = "Worldwide", max_per_keyword: int = 10) -> list[dict]:
    """
    Scrape LinkedIn jobs for each keyword.
    Returns a list of normalized lead dicts.
    """
    keywords = keywords or config.LINKEDIN_KEYWORDS
    all_leads = []
    seen_ids = set()

    for keyword in keywords[:3]:  # cap at 3 keywords to reduce block risk
        try:
            params = {
                "keywords": keyword,
                "location": location,
                "f_WT": "2",  # remote filter
                "start": "0",
            }
            resp = requests.get(GUEST_API, params=params, headers=_get_headers(), timeout=15)

            if resp.status_code == 429:
                print(f"[LinkedIn] Rate limited for '{keyword}'. Skipping.")
                time.sleep(10)
                continue

            if resp.status_code != 200:
                print(f"[LinkedIn] HTTP {resp.status_code} for '{keyword}'")
                continue

            html = resp.text
            if len(html) < 100 or _is_blocked(html):
                print(f"[LinkedIn] Blocked or empty response for '{keyword}'")
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("li")[:max_per_keyword]

            for card in cards:
                title_el   = card.find("h3", class_=re.compile("base-search-card__title"))
                company_el = card.find("h4", class_=re.compile("base-search-card__subtitle"))
                loc_el     = card.find("span", class_=re.compile("job-search-card__location"))
                link_el    = card.find("a", class_=re.compile("base-card__full-link"))

                if not title_el or not link_el:
                    continue

                title   = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else ""
                loc     = loc_el.get_text(strip=True) if loc_el else location
                url     = link_el.get("href", "").split("?")[0]
                job_id  = _extract_job_id(url)

                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                lead = {
                    "id": f"linkedin-{job_id}",
                    "platform": "linkedin",
                    "title": title,
                    "company": company,
                    "url": url,
                    "budget": 0,
                    "proposals": 0,
                    "client_spend": 0,
                    "payment_verified": False,
                    "description": f"{title} at {company} — {loc}",
                    "posted_at": "",
                    "location": loc,
                    "keyword": keyword,
                    "niche": "",
                    "type": "job",
                }
                all_leads.append(lead)

            print(f"[LinkedIn] '{keyword}' → {len(cards)} jobs found")
            time.sleep(random.uniform(3.0, 5.5))

        except Exception as e:
            print(f"[LinkedIn] Error for keyword '{keyword}': {e}")
            continue

    return all_leads
