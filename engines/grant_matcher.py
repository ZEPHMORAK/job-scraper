"""
engines/grant_matcher.py — Grant Match Engine
Matches researcher profiles to available grants using multi-signal scoring.
"""

ACADEMIC_TITLE_WEIGHT = {
    "professor": 1.0,
    "associate professor": 0.95,
    "assistant professor": 0.9,
    "postdoctoral": 0.85,
    "postdoc": 0.85,
    "phd": 0.75,
    "doctoral": 0.75,
    "researcher": 0.7,
    "lecturer": 0.65,
}

GEO_MATCH = {
    "global": 1.0,
    "africa": 0.9,
    "nigeria": 0.85,
    "usa": 0.7,
    "uk": 0.7,
    "europe": 0.7,
    "uk + partner countries": 0.8,
    "global (us institution preferred)": 0.75,
}


def match_grants(researcher: dict, grants: list[dict]) -> list[dict]:
    """
    Score all grants against a researcher profile.
    Returns list of matches with score >= 50, sorted by score descending.
    """
    matches = []

    for grant in grants:
        score, reasons = _score_match(researcher, grant)
        if score >= 50:
            matches.append({
                "grant": grant,
                "match_score": score,
                "reasons": reasons,
                "priority": _match_priority(score),
            })

    return sorted(matches, key=lambda x: x["match_score"], reverse=True)


def _score_match(researcher: dict, grant: dict) -> tuple[float, list]:
    score = 0.0
    reasons = []

    title    = researcher.get("title", "").lower()
    keywords = [k.lower() for k in researcher.get("keywords", [])]
    field    = researcher.get("matched_field", "").lower()
    country  = researcher.get("location", "").lower()
    kw_text  = " ".join(keywords + [field, title])

    grant_fields = [f.lower() for f in grant.get("fields", [])]
    grant_focus  = " ".join([f.lower() for f in grant.get("focus", [])])
    grant_geo    = grant.get("geo", "global").lower()
    grant_name   = grant.get("name", "").lower()

    # ── 1. Research Topic Alignment (0–40 pts) ───────────────────────────────
    topic_score = 0

    # Direct field match
    if "all fields" in grant_fields:
        topic_score += 25
        reasons.append("Open to all research fields (+25)")
    else:
        for gf in grant_fields:
            if gf in field or field in gf:
                topic_score += 30
                reasons.append(f"Direct field match: {gf} (+30)")
                break

    # Keyword match in grant focus
    keyword_hits = sum(1 for kw in keywords if kw in grant_focus)
    kw_bonus = min(keyword_hits * 5, 15)
    if kw_bonus > 0:
        topic_score += kw_bonus
        reasons.append(f"Keyword alignment ({keyword_hits} hits) (+{kw_bonus})")

    score += min(topic_score, 40)

    # ── 2. Academic Title / Experience (0–20 pts) ────────────────────────────
    title_score = 0
    for t, weight in ACADEMIC_TITLE_WEIGHT.items():
        if t in title:
            title_score = weight * 20
            reasons.append(f"Title match: {t} (+{title_score:.0f})")
            break
    score += title_score

    # ── 3. Geographic Eligibility (0–20 pts) ────────────────────────────────
    geo_score = 0
    for geo_key, geo_weight in GEO_MATCH.items():
        if geo_key in grant_geo:
            if geo_key == "global":
                geo_score = 20
                reasons.append("Globally eligible (+20)")
                break
            elif geo_key in country or country in geo_key:
                geo_score = geo_weight * 20
                reasons.append(f"Geographic match: {geo_key} (+{geo_score:.0f})")
                break

    if geo_score == 0:
        # Default moderate score for unknown geography
        geo_score = 10
    score += geo_score

    # ── 4. Publication Strength (0–10 pts) ──────────────────────────────────
    publications = researcher.get("publications", 0)
    if publications >= 20:
        score += 10
        reasons.append("High publication count (+10)")
    elif publications >= 10:
        score += 7
        reasons.append("Good publication record (+7)")
    elif publications >= 3:
        score += 4
        reasons.append("Some publications (+4)")

    # ── 5. Collaboration Requirement (0–10 pts) ──────────────────────────────
    collab_req = grant.get("collaboration", "").lower()
    has_collab = bool(researcher.get("collaborators") or researcher.get("international"))
    if "not required" in collab_req:
        score += 10
        reasons.append("No collaboration required (+10)")
    elif has_collab:
        score += 7
        reasons.append("Researcher has collaboration signals (+7)")
    else:
        score += 3
        reasons.append("Collaboration potential (+3)")

    return round(min(score, 100), 1), reasons


def _match_priority(score: float) -> str:
    if score >= 85:
        return "EXCELLENT"
    elif score >= 70:
        return "STRONG"
    elif score >= 50:
        return "MODERATE"
    return "POOR"
