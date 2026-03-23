"""
scrapers/indeed.py — Scrape Indeed jobs via public RSS feed.
No authentication required. Stable and reliable.
"""
import re
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import config

RSS_URL = "https://www.indeed.com/rss"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_date(pub_date_str: str) -> datetime | None:
    if not pub_date_str:
        return None
    try:
        return datetime.strptime(pub_date_str.strip(), "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        try:
            return datetime.strptime(pub_date_str.strip()[:25], "%a, %d %b %Y %H:%M:%S")
        except ValueError:
            return None


def _is_recent(pub_date_str: str, max_hours: float = 4.0) -> bool:
    dt = _parse_date(pub_date_str)
    if not dt:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - dt) <= timedelta(hours=max_hours)


def scrape_indeed(keywords: list[str] = None, location: str = "remote", max_per_keyword: int = 15) -> list[dict]:
    """
    Scrape Indeed RSS for each keyword.
    Returns a list of normalized lead dicts.
    """
    keywords = keywords or config.LINKEDIN_KEYWORDS  # reuse same keywords
    all_leads = []
    seen_guids = set()

    for keyword in keywords[:5]:
        try:
            params = {
                "q": keyword,
                "l": location,
                "sort": "date",
                "fromage": "1",  # posted within last 1 day
            }
            resp = requests.get(RSS_URL, params=params, headers=HEADERS, timeout=15)

            if resp.status_code != 200:
                print(f"[Indeed] HTTP {resp.status_code} for '{keyword}'")
                continue

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                print(f"[Indeed] No channel in RSS for '{keyword}'")
                continue

            items = channel.findall("item")[:max_per_keyword]
            count = 0

            for item in items:
                title    = (item.findtext("title") or "").strip()
                url      = (item.findtext("link") or "").strip()
                guid     = (item.findtext("guid") or url).strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                desc_raw = (item.findtext("description") or "")
                desc     = _strip_html(desc_raw)

                # Extract company from title (Indeed format: "Job Title - Company")
                company = ""
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else ""

                if not guid or guid in seen_guids:
                    continue
                seen_guids.add(guid)

                lead = {
                    "id": f"indeed-{guid[-20:].replace('/', '-')}",
                    "platform": "indeed",
                    "title": title,
                    "company": company,
                    "url": url,
                    "budget": 0,
                    "proposals": 0,
                    "client_spend": 0,
                    "payment_verified": False,
                    "description": desc[:500],
                    "posted_at": pub_date,
                    "location": location,
                    "keyword": keyword,
                    "niche": "",
                    "type": "job",
                }
                all_leads.append(lead)
                count += 1

            print(f"[Indeed] '{keyword}' -> {count} jobs found")
            time.sleep(random.uniform(1.5, 3.0))

        except ET.ParseError as e:
            print(f"[Indeed] XML parse error for '{keyword}': {e}")
            continue
        except Exception as e:
            print(f"[Indeed] Error for '{keyword}': {e}")
            continue

    return all_leads
