"""
scrapers/google_scholar.py — Google Scholar researcher discovery
Uses DDG to find Scholar author profiles and university faculty pages.
"""
import re
import hashlib
import time
from core.ddg_search import ddg_search, make_session
from core.email_extractor import extract_email_from_text

SCHOLAR_QUERIES = [
    "site:scholar.google.com professor artificial intelligence research",
    "site:scholar.google.com professor public health Africa",
    "site:scholar.google.com associate professor climate science",
    "site:scholar.google.com phd researcher biotechnology",
    "site:scholar.google.com professor digital health Nigeria",
    "site:scholar.google.com researcher machine learning Africa",
    "professor artificial intelligence university faculty page email",
    "assistant professor climate change research university email contact",
    "postdoctoral researcher public health university email",
    "professor biotechnology university department email contact",
    "associate professor sustainable energy university faculty",
    "researcher digital health university email Africa",
]

TITLE_PATTERNS = [
    "professor", "associate professor", "assistant professor",
    "postdoctoral", "postdoc", "phd researcher", "research fellow",
    "senior lecturer", "lecturer", "research scientist",
]

KEYWORD_SIGNALS = [
    "artificial intelligence", "machine learning", "deep learning",
    "climate", "health", "biotechnology", "energy", "sustainability",
    "agriculture", "cybersecurity", "genomics", "public health",
    "data science", "neural", "epidemiology", "bioinformatics",
]


def _extract_keywords(text: str) -> list:
    text = text.lower()
    return [kw for kw in KEYWORD_SIGNALS if kw in text]


def _extract_publications(text: str) -> int:
    """Try to parse publication count from snippet."""
    m = re.search(r"(\d+)\s*(?:publications?|papers?|articles?|cited)", text, re.I)
    if m:
        return int(m.group(1))
    return 0


def _detect_title(text: str) -> str:
    text_lower = text.lower()
    for t in TITLE_PATTERNS:
        if t in text_lower:
            return t.title()
    return "Researcher"


def scrape_google_scholar(max_per_query: int = 5) -> list[dict]:
    leads = []
    seen = set()
    session = make_session()

    for query in SCHOLAR_QUERIES:
        results = ddg_search(session, query, max_per_query)
        for r in results:
            url = r["url"]
            if url in seen:
                continue

            # Filter to academic sources only
            if not any(d in url for d in [
                "scholar.google", ".edu", ".ac.uk", ".ac.ng", ".ac.za",
                "researchgate.net", "academia.edu", "orcid.org",
            ]):
                continue

            seen.add(url)
            text = f"{r['title']} {r['snippet']}"
            keywords = _extract_keywords(text)
            if not keywords:
                continue  # skip non-research results

            email = extract_email_from_text(r["snippet"])
            lead_id = "scholar_" + hashlib.md5(url.encode()).hexdigest()[:12]
            detected_title = _detect_title(text)
            pubs = _extract_publications(r["snippet"])

            # Extract university from URL or title
            university = ""
            for pattern in [r"(\w+\.edu)", r"(\w+\.ac\.\w+)"]:
                m = re.search(pattern, url)
                if m:
                    university = m.group(1)
                    break

            leads.append({
                "id": lead_id,
                "platform": "google_scholar",
                "type": "lead",
                "niche": "academic",
                "title": r["title"][:100],
                "description": r["snippet"][:300],
                "url": url,
                "linkedin": "",
                "company": university,
                "location": "",
                "email": email or "",
                "phone": "",
                "department": "",
                "keywords": keywords,
                "publications": pubs,
                "academic_title": detected_title,
                "budget": 0,
                "proposals": 0,
                "client_spend": 0,
                "payment_verified": False,
                "score": 0,
            })
        time.sleep(1.5)

    print(f"[GoogleScholar] {len(leads)} researcher profiles found")
    return leads
