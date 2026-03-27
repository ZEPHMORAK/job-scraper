"""
filters/lead_filter.py — Lead scoring engine (new 4-niche model)

Scoring signals:
  Decision maker identified  → +2
  Business website present   → +1
  Email found                → +1
  LinkedIn profile found     → +1
  Website automation gap     → +2
  Company growth signal      → +2
  Academic .edu email        → +3
  Professor / PhD title      → +3
  University affiliation     → +2
"""
import config

DECISION_MAKER_KWS = [
    "ceo", "founder", "managing director", "director", "partner",
    "professor", "phd", "principal", "attorney", "solicitor",
    "chief executive", "president", "managing partner", "head of",
    "barrister", "advocate", "counsel",
]

GROWTH_KWS = [
    "growing", "hiring", "expanded", "new office", "launched",
    "funding", "series", "investment", "award", "ranked",
    "top firm", "leading", "fastest growing",
]

ACADEMIC_DOMAINS = [".edu", ".ac.uk", ".edu.ng", ".ac.za"]
ACADEMIC_TITLES = [
    "professor", "phd", "doctoral", "research fellow",
    "postdoc", "postdoctoral", "assistant professor",
    "associate professor", "phd candidate", "phd student",
]


def score_lead(lead: dict, web_intel: dict = None) -> int:
    """
    Score a lead 1-10 using the new 4-niche scoring model.
    web_intel is optional (from website_intelligence.analyze_website).
    """
    if web_intel is None:
        web_intel = {}

    score = 0
    text = f"{lead.get('title', '')} {lead.get('description', '')}".lower()
    niche = lead.get("niche", "")
    email = lead.get("email", "")
    url = lead.get("url", "")

    # Decision maker identified (+2)
    if any(kw in text for kw in DECISION_MAKER_KWS):
        score += 2

    # Business website accessible (+1)
    if web_intel.get("accessible") or (url and url.startswith("http")):
        score += 1

    # Email found (+1)
    if email:
        score += 1

    # LinkedIn found (+1)
    if lead.get("linkedin"):
        score += 1

    # Website automation gap (+2)
    gap = web_intel.get("automation_gap_score", 0)
    if gap >= 2:
        score += 2
    elif gap >= 1:
        score += 1

    # Growth signal (+2)
    if any(kw in text for kw in GROWTH_KWS):
        score += 2

    # Academic-specific signals
    if niche == "academic":
        if any(d in email for d in ACADEMIC_DOMAINS):
            score += 3
        if any(kw in text for kw in ACADEMIC_TITLES):
            score += 3
        if any(d in url for d in ACADEMIC_DOMAINS):
            score += 2

    return min(10, max(1, score))


def filter_leads(leads: list[dict], web_intel_map: dict = None) -> list[dict]:
    """
    Score and filter leads. Only returns leads with score >= MIN_SCORE.
    web_intel_map: dict of lead_id -> web_intel (optional)
    """
    if web_intel_map is None:
        web_intel_map = {}

    if config.DEBUG_MODE:
        print(f"[Filter] DEBUG MODE — passing all {len(leads)} leads")
        for lead in leads:
            intel = web_intel_map.get(lead["id"], {})
            lead["score"] = score_lead(lead, intel)
            print(f"  -> score={lead['score']}/10 niche={lead.get('niche','?')} | '{lead.get('title','')[:55]}'")
        return leads

    qualified = []
    dropped = 0

    for lead in leads:
        intel = web_intel_map.get(lead["id"], {})
        score = score_lead(lead, intel)
        lead["score"] = score

        if score < config.MIN_SCORE:
            dropped += 1
            continue

        print(f"[Filter] QUALIFIED {score}/10 [{lead.get('niche','?')}] '{lead.get('title','')[:55]}'")
        qualified.append(lead)

    print(f"[Filter] {len(qualified)} qualified, {dropped} dropped from {len(leads)} total")
    return qualified
