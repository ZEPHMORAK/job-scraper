"""
core/researcher_scorer.py — Lead Scoring Engine for academic researchers
Scores 1-10 based on research activity, publications, field, and signals.
"""
import config

ACADEMIC_TITLES = {
    "professor": 3.0,
    "associate professor": 2.5,
    "assistant professor": 2.0,
    "postdoctoral": 1.5,
    "postdoc": 1.5,
    "research fellow": 1.5,
    "phd researcher": 1.0,
    "doctoral": 1.0,
    "senior lecturer": 1.5,
    "lecturer": 1.0,
}

ELITE_UNIVERSITIES = [
    "oxford", "cambridge", "mit", "harvard", "stanford", "yale",
    "imperial", "ucl", "edinburgh", "toronto", "melbourne",
    "cape town", "ibadan", "lagos", "nairobi", "accra",
]

ACADEMIC_DOMAINS = [".edu", ".ac.uk", ".ac.ng", ".ac.za"]

HIGH_IMPACT_FIELDS = [
    "artificial intelligence", "machine learning", "climate", "health",
    "biotechnology", "genomics", "energy", "sustainability", "public health",
    "digital health", "bioinformatics",
]


def score_researcher(researcher: dict, field_data: dict = None) -> int:
    """
    Score a researcher lead 1-10.
    Uses: title, publications, field, email, university, collaboration signals.
    """
    if field_data is None:
        field_data = {}

    score = 0
    text = f"{researcher.get('title', '')} {researcher.get('description', '')}".lower()
    url = researcher.get("url", "").lower()
    email = researcher.get("email", "")
    keywords = [k.lower() for k in researcher.get("keywords", [])]
    publications = researcher.get("publications", 0)

    # ── Academic Title (0–3 pts) ──────────────────────────────────────────────
    for title, pts in ACADEMIC_TITLES.items():
        if title in text:
            score += pts
            break

    # ── Publication Volume (0–2 pts) ─────────────────────────────────────────
    if publications >= 20:
        score += 2
    elif publications >= 10:
        score += 1.5
    elif publications >= 3:
        score += 1

    # ── Research Field Funding Score (0–2 pts) ───────────────────────────────
    field_score = field_data.get("opportunity_score", 5.0)
    if field_score >= 9.0:
        score += 2
    elif field_score >= 7.5:
        score += 1.5
    elif field_score >= 6.0:
        score += 1

    # ── Email / Contact Found (0–1 pt) ───────────────────────────────────────
    if email:
        if any(d in email for d in ACADEMIC_DOMAINS):
            score += 1  # academic email = confirmed
        else:
            score += 0.5

    # ── University Reputation (0–1 pt) ───────────────────────────────────────
    company = researcher.get("company", "").lower()
    if any(u in company or u in url for u in ELITE_UNIVERSITIES):
        score += 1

    # ── Academic domain URL (0–0.5 pt) ──────────────────────────────────────
    if any(d in url for d in ACADEMIC_DOMAINS):
        score += 0.5

    # ── High-impact field keywords (0–1 pt) ──────────────────────────────────
    if any(kw in text for kw in HIGH_IMPACT_FIELDS) or any(kw in keywords for kw in HIGH_IMPACT_FIELDS):
        score += 1

    return min(10, max(1, round(score)))


def classify_researcher(score: int) -> str:
    if score >= 9:
        return "ELITE"
    elif score >= 7:
        return "HIGH VALUE"
    elif score >= 5:
        return "MODERATE VALUE"
    return "LOW VALUE"
