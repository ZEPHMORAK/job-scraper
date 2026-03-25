"""
filters/lead_filter.py — Smart filter + scoring engine
Hard filters drop unqualified leads; scoring ranks the rest 1–10.
Only leads with score >= MIN_SCORE (default 7) are forwarded to Telegram.
"""
import re
from datetime import datetime, timezone, timedelta
import config

# Keywords that signal the lead matches target niches
NICHE_KEYWORDS = {
    "coaching": ["coach", "coaching", "life coach", "business coach", "executive coach",
                 "online course", "e-learning", "membership site", "mastermind"],
    "real estate": ["real estate", "realty", "property", "realtor", "mls", "listing",
                    "mortgage", "landlord", "property management", "airbnb"],
    "consultant": ["consultant", "consulting", "advisor", "advisory", "strategy"],
    "automation": ["automation", "automate", "workflow", "zapier", "make.com",
                   "n8n", "crm", "pipeline"],
}

# Urgency signals
URGENCY_KEYWORDS = ["asap", "urgent", "immediately", "right away", "today", "this week",
                    "fast", "quickly", "deadline", "time-sensitive"]


# ─── Hard Filters ─────────────────────────────────────────────────────────────

def _passes_hard_filters(lead: dict) -> tuple[bool, str]:
    """
    Returns (passes: bool, reason: str).
    For Upwork leads, all hard filter rules apply.
    For LinkedIn/GMaps, only budget check is skipped (no budget data available).
    """
    platform = lead.get("platform", "")

    # Upwork-specific hard filters
    if platform == "upwork":
        budget = lead.get("budget", 0)
        if budget > 0 and budget < config.MIN_BUDGET:
            return False, f"Budget ${budget} below minimum ${config.MIN_BUDGET}"

        proposals = lead.get("proposals", 0)
        if proposals >= 50:
            return False, f"Too competitive — {proposals} proposals already"

        posted_at = lead.get("posted_at", "")
        if not _is_recent(posted_at, max_hours=24.0):
            return False, "Posted more than 24 hours ago"

    # LinkedIn / Indeed — only block if clearly too many proposals
    if platform in ("linkedin", "indeed"):
        proposals = lead.get("proposals", 0)
        if proposals >= 50:
            return False, "Too many applicants"

    # Real estate and academic leads always pass hard filters
    if platform in ("real_estate", "academic"):
        return True, ""

    return True, ""


def _is_recent(posted_at: str, max_hours: float = 2.0) -> bool:
    if not posted_at:
        return True
    try:
        dt = datetime.strptime(posted_at.strip(), "%a, %d %b %Y %H:%M:%S %z")
        return (datetime.now(timezone.utc) - dt) <= timedelta(hours=max_hours)
    except ValueError:
        return True


# ─── Scoring ──────────────────────────────────────────────────────────────────

def score_lead(lead: dict) -> tuple[int, str]:
    """
    Score a lead 1–10.
    Returns (score, niche_detected).
    """
    score = 0
    niche = ""

    # Budget score (0–3 pts)
    budget = lead.get("budget", 0)
    if budget >= 1000:
        score += 3
    elif budget >= 500:
        score += 2
    elif budget >= 100:
        score += 1

    # Niche match (0–2 pts)
    text = f"{lead.get('title', '')} {lead.get('description', '')}".lower()
    for niche_name, keywords in NICHE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            score += 2
            niche = niche_name
            break

    # Urgency signals (0–1 pt)
    if any(kw in text for kw in URGENCY_KEYWORDS):
        score += 1

    # Competition score (0–2 pts)
    proposals = lead.get("proposals", 0)
    if proposals < 5:
        score += 2
    elif proposals < 10:
        score += 1

    # Real estate + academic leads: base score 6 (no budget/proposals data available)
    if lead.get("platform") in ("real_estate", "academic"):
        score = max(score, 6)
        if lead.get("email"):
            score = min(10, score + 2)  # bonus for having an email

    # Google Maps leads get a base score of 6 (no proposals/budget data)
    if lead.get("platform") == "gmaps":
        score = max(score, 6)
        rating = lead.get("rating", 0)
        reviews = lead.get("review_count", 0)
        if rating >= 4.0 and reviews >= 50:
            score = min(10, score + 2)

    # Cap at 10
    score = min(10, max(1, score))
    return score, niche


# ─── Main Filter Function ──────────────────────────────────────────────────────

def filter_leads(leads: list[dict]) -> list[dict]:
    """
    Apply hard filters + scoring to a list of raw leads.
    Returns only qualified leads (score >= MIN_SCORE) with score/niche attached.
    If DEBUG_MODE=True, all leads pass through regardless of score.
    """
    if config.DEBUG_MODE:
        print(f"[Filter] DEBUG MODE — skipping all filters, passing {len(leads)} leads through")
        for lead in leads:
            score, niche = score_lead(lead)
            lead["score"] = score
            lead["niche"] = niche or lead.get("niche", "")
            print(f"  -> score={score}/10 | '{lead.get('title', '')[:60]}'")
        return leads

    qualified = []
    dropped = 0

    for lead in leads:
        passes, reason = _passes_hard_filters(lead)
        if not passes:
            print(f"[Filter] DROPPED '{lead.get('title', '')[:50]}' — {reason}")
            dropped += 1
            continue

        score, niche = score_lead(lead)
        lead["score"] = score
        lead["niche"] = niche or lead.get("niche", "")

        if score < config.MIN_SCORE:
            print(f"[Filter] LOW SCORE {score}/10 — '{lead.get('title', '')[:50]}'")
            dropped += 1
            continue

        print(f"[Filter] QUALIFIED score={score}/10 niche={lead['niche'] or 'unknown'} — '{lead.get('title', '')[:50]}'")
        qualified.append(lead)

    print(f"[Filter] {len(qualified)} qualified, {dropped} dropped from {len(leads)} total")
    return qualified
