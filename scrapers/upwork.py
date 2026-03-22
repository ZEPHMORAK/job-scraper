"""
scrapers/upwork.py — Scrape Upwork jobs via public RSS feed
No authentication required. Parses XML with built-in xml.etree.ElementTree.
"""
import re
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

RSS_URL = "https://www.upwork.com/ab/feed/jobs/rss"


def _parse_budget(description: str) -> float:
    """Extract budget amount from Upwork RSS description HTML."""
    patterns = [
        r"Budget:\s*\$([0-9,]+)",
        r"Hourly Range:\s*\$([0-9.]+)",
        r"\$([0-9,]+)-\$([0-9,]+)",
    ]
    for pat in patterns:
        m = re.search(pat, description, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except (ValueError, IndexError):
                pass
    return 0.0


def _parse_proposals(description: str) -> int:
    """Extract proposal count from description."""
    m = re.search(r"Proposals:\s*(\d+)", description, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return 0


def _parse_client_spend(description: str) -> float:
    """Extract client total spent from description."""
    m = re.search(r"Total Spent:\s*\$([0-9,]+)", description, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return 0.0


def _payment_verified(description: str) -> bool:
    return "Payment verified" in description


def _parse_date(pub_date_str: str) -> datetime | None:
    """Parse RSS pubDate like 'Mon, 21 Mar 2026 14:00:00 +0000'."""
    if not pub_date_str:
        return None
    try:
        return datetime.strptime(pub_date_str.strip(), "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        return None


def _is_recent(pub_date_str: str, max_hours: float = 2.0) -> bool:
    """Return True if posted within max_hours."""
    dt = _parse_date(pub_date_str)
    if not dt:
        return True  # can't tell — let the lead through
    now = datetime.now(timezone.utc)
    return (now - dt) <= timedelta(hours=max_hours)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def scrape_upwork(keywords: list[str] = None, max_per_keyword: int = 15) -> list[dict]:
    """
    Scrape Upwork RSS for each keyword.
    Returns a list of normalized lead dicts.
    """
    keywords = keywords or config.UPWORK_KEYWORDS
    all_leads = []
    seen_guids = set()

    for keyword in keywords[:config.DAILY_UPWORK_LIMIT]:
        try:
            params = {"q": keyword, "sort": "recency"}
            resp = requests.get(RSS_URL, params=params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"[Upwork] HTTP {resp.status_code} for keyword '{keyword}'")
                continue

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                continue

            items = channel.findall("item")[:max_per_keyword]
            for item in items:
                title    = (item.findtext("title") or "").strip()
                url      = (item.findtext("link") or "").strip()
                guid     = (item.findtext("guid") or url).strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                desc_raw = (item.findtext("description") or "")
                desc     = _strip_html(desc_raw)

                if not guid or guid in seen_guids:
                    continue
                seen_guids.add(guid)

                budget   = _parse_budget(desc)
                proposals = _parse_proposals(desc)
                client_spend = _parse_client_spend(desc)
                pv       = _payment_verified(desc)

                lead = {
                    "id": f"upwork-{guid}",
                    "platform": "upwork",
                    "title": title,
                    "company": "",
                    "url": url,
                    "budget": budget,
                    "proposals": proposals,
                    "client_spend": client_spend,
                    "payment_verified": pv,
                    "description": desc[:500],
                    "posted_at": pub_date,
                    "keyword": keyword,
                    "niche": "",
                    "type": "job",
                }
                all_leads.append(lead)

            print(f"[Upwork] '{keyword}' → {len(items)} jobs found")
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"[Upwork] Error for keyword '{keyword}': {e}")
            continue

    return all_leads
