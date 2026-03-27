"""
core/opportunity_detector.py — Score and classify lead opportunities
"""


DECISION_MAKER_KWS = [
    "ceo", "founder", "managing director", "director", "partner",
    "professor", "phd", "principal", "attorney", "solicitor",
    "chief executive", "president", "managing partner", "head of",
]

GROWTH_KWS = [
    "growing", "hiring", "expanded", "new office", "launched",
    "funding", "series a", "series b", "investment", "award",
    "ranked", "top firm", "leading", "fastest growing",
]

ACADEMIC_DOMAINS = [".edu", ".ac.uk", ".edu.ng", ".ac.za"]
ACADEMIC_TITLES = [
    "professor", "phd", "doctoral", "research fellow",
    "postdoc", "postdoctoral", "assistant professor",
    "associate professor", "phd candidate", "phd student",
]


def detect_opportunity(lead: dict, web_intel: dict) -> dict:
    """
    Calculate opportunity score and classify priority.
    Returns: {opportunity_score, priority, reasoning}
    """
    score = 0
    reasoning = []

    text = f"{lead.get('title', '')} {lead.get('description', '')}".lower()
    niche = lead.get("niche", "")
    email = lead.get("email", "")
    url = lead.get("url", "")

    # Decision maker identified (+2)
    if any(kw in text for kw in DECISION_MAKER_KWS):
        score += 2
        reasoning.append("Decision maker identified (+2)")

    # Business website accessible (+1)
    if web_intel.get("accessible"):
        score += 1
        reasoning.append("Website accessible (+1)")

    # Email found (+1)
    if email:
        score += 1
        reasoning.append("Email found (+1)")

    # LinkedIn profile (+1)
    if lead.get("linkedin"):
        score += 1
        reasoning.append("LinkedIn found (+1)")

    # Automation gap detected (+2 or +1)
    gap = web_intel.get("automation_gap_score", 0)
    if gap >= 3:
        score += 2
        missing = ", ".join(web_intel.get("signals_missing", []))
        reasoning.append(f"Automation gaps (+2): {missing}")
    elif gap >= 1:
        score += 1
        reasoning.append("Some automation gaps (+1)")

    # Growth signal (+2)
    if any(kw in text for kw in GROWTH_KWS):
        score += 2
        reasoning.append("Growth signal detected (+2)")

    # Academic-specific scoring
    if niche == "academic":
        if any(d in email for d in ACADEMIC_DOMAINS):
            score += 3
            reasoning.append("Academic .edu/.ac email (+3)")
        if any(kw in text for kw in ACADEMIC_TITLES):
            score += 3
            reasoning.append("Academic title (PhD/Professor) (+3)")
        if any(d in url for d in ACADEMIC_DOMAINS):
            score += 2
            reasoning.append("University domain affiliation (+2)")

    score = min(10, score)

    if score >= 8:
        priority = "HIGH"
    elif score >= 6:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "opportunity_score": score,
        "priority": priority,
        "reasoning": reasoning,
    }
