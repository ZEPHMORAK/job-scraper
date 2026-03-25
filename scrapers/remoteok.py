"""
scrapers/remoteok.py — Scrape remote jobs via RemoteOK public API.
Free, no auth required. Returns JSON directly.
API: https://remoteok.com/api
"""
import time
import requests
import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

API_URL = "https://remoteok.com/api"

NICHE_KEYWORDS = [
    "automat", "chatbot", "ai ", "crm", "workflow", "scraping",
    "virtual assistant", "lead gen", "integration", "zapier",
    "n8n", "make.com", "python", "bot", "data pipeline",
]


def scrape_remoteok(max_leads: int = 30) -> list[dict]:
    """
    Fetch latest remote jobs from RemoteOK API.
    Filters for automation/AI-related roles.
    Returns normalized lead dicts.
    """
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            print(f"[RemoteOK] HTTP {resp.status_code}")
            return []

        jobs = resp.json()
        # First item is a legal note dict, skip it
        jobs = [j for j in jobs if isinstance(j, dict) and j.get("id")]

    except Exception as e:
        print(f"[RemoteOK] Error: {e}")
        return []

    leads = []
    seen_ids = set()

    for job in jobs:
        if len(leads) >= max_leads:
            break

        job_id = str(job.get("id", ""))
        if not job_id or job_id in seen_ids:
            continue

        title = job.get("position", "").strip()
        company = job.get("company", "").strip()
        tags = " ".join(job.get("tags") or []).lower()
        description = job.get("description", "") or ""
        url = job.get("url", "") or f"https://remoteok.com/remote-jobs/{job_id}"
        salary_min = job.get("salary_min") or 0
        salary_max = job.get("salary_max") or 0
        budget = salary_min or salary_max

        # Filter: only automation/AI relevant jobs
        text = f"{title} {tags} {description[:200]}".lower()
        if not any(kw in text for kw in NICHE_KEYWORDS):
            continue

        seen_ids.add(job_id)
        lead = {
            "id": f"remoteok-{job_id}",
            "platform": "remoteok",
            "title": title,
            "company": company,
            "url": url,
            "budget": budget,
            "proposals": 0,
            "client_spend": 0,
            "payment_verified": True,  # RemoteOK verifies companies
            "description": f"{title} at {company}. {description[:300]}",
            "posted_at": job.get("date", ""),
            "keyword": tags[:80],
            "niche": "",
            "type": "job",
        }
        leads.append(lead)

    print(f"[RemoteOK] {len(leads)} relevant jobs found")
    return leads
