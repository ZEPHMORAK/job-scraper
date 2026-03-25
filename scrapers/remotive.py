"""
scrapers/remotive.py — Scrape remote jobs via Remotive public API.
Free, no auth required. Returns JSON.
API: https://remotive.com/api/remote-jobs
"""
import requests
import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

API_URL = "https://remotive.com/api/remote-jobs"

# Categories that match our niche
CATEGORIES = [
    "software-dev", "devops-sysadmin", "data",
    "product", "marketing",
]

NICHE_KEYWORDS = [
    "automat", "chatbot", "ai", "crm", "workflow",
    "scraping", "virtual assistant", "lead", "integration",
    "python", "bot", "n8n", "zapier", "make.com",
]


def scrape_remotive(max_leads: int = 20) -> list[dict]:
    """
    Fetch jobs from Remotive API across relevant categories.
    Returns normalized lead dicts.
    """
    leads = []
    seen_ids = set()

    for category in CATEGORIES:
        if len(leads) >= max_leads:
            break
        try:
            resp = requests.get(
                API_URL,
                params={"category": category, "limit": 20},
                headers=HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[Remotive] HTTP {resp.status_code} for category '{category}'")
                continue

            jobs = resp.json().get("jobs", [])

            for job in jobs:
                if len(leads) >= max_leads:
                    break

                job_id = str(job.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue

                title = job.get("title", "").strip()
                company = job.get("company_name", "").strip()
                description = job.get("description", "") or ""
                url = job.get("url", "")
                salary = job.get("salary", "") or ""
                tags = " ".join(job.get("tags") or []).lower()

                # Filter for niche relevance
                text = f"{title} {tags} {description[:200]}".lower()
                if not any(kw in text for kw in NICHE_KEYWORDS):
                    continue

                # Try to extract budget from salary string
                budget = 0
                import re
                m = re.search(r"\$([0-9,]+)", salary)
                if m:
                    try:
                        budget = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass

                seen_ids.add(job_id)
                lead = {
                    "id": f"remotive-{job_id}",
                    "platform": "remotive",
                    "title": title,
                    "company": company,
                    "url": url,
                    "budget": budget,
                    "proposals": 0,
                    "client_spend": 0,
                    "payment_verified": True,
                    "description": f"{title} at {company}. {description[:300]}",
                    "posted_at": job.get("publication_date", ""),
                    "keyword": tags[:80],
                    "niche": "",
                    "type": "job",
                }
                leads.append(lead)

            print(f"[Remotive] '{category}' -> {len([j for j in jobs])} jobs checked")

        except Exception as e:
            print(f"[Remotive] Error for '{category}': {e}")
            continue

    print(f"[Remotive] {len(leads)} relevant jobs total")
    return leads
