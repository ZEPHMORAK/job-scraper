"""
engines/researcher_profile.py — Researcher Intelligence Profile Engine
Builds a concise intelligence profile for each qualified researcher using AI.
"""
from ai._client import chat
import config


def build_researcher_profile(researcher: dict, field_data: dict) -> dict:
    """
    Build a research intelligence profile using GPT-4o.
    Returns enriched profile dict.
    """
    system = (
        "You are a research intelligence analyst. "
        "Given a researcher's basic details, generate a concise intelligence profile. "
        "Be factual, structured, and professional. Keep each section to 2-3 sentences max."
    )

    user = f"""
Researcher Details:
Name: {researcher.get('title', 'Unknown')}
University: {researcher.get('company', 'Unknown')}
Department: {researcher.get('department', 'Unknown')}
Research Field: {researcher.get('matched_field', 'Unknown')}
Keywords: {', '.join(researcher.get('keywords', []))}
Publications: ~{researcher.get('publications', 'unknown')}
Location: {researcher.get('location', 'Unknown')}
Description: {researcher.get('description', '')}

Generate a JSON response with these exact keys:
- academic_background (2 sentences)
- top_research_themes (list of 3-5 bullet points)
- likely_research_interests (2 sentences)
- publication_strength (1 sentence assessment)
- potential_funding_areas (list of 3 funding areas)
- collaboration_potential (1 sentence)
- consultant_summary (3 sentences — what a consultant should know before contacting this researcher)

Return only valid JSON.
""".strip()

    try:
        raw = chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        import json
        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            profile_data = json.loads(raw[start:end])
        else:
            profile_data = _fallback_profile(researcher)
    except Exception:
        profile_data = _fallback_profile(researcher)

    return {
        **profile_data,
        "matched_field": field_data.get("field", "General Research"),
        "field_funding": field_data.get("estimated_funding", "N/A"),
        "field_opportunity_score": field_data.get("opportunity_score", 5.0),
        "field_growth": field_data.get("growth_trend", "Stable"),
    }


def _fallback_profile(researcher: dict) -> dict:
    field = researcher.get("matched_field", "their research area")
    name = researcher.get("title", "This researcher")
    return {
        "academic_background": f"{name} is an academic researcher in {field}.",
        "top_research_themes": researcher.get("keywords", ["Research", "Academia"]),
        "likely_research_interests": f"Based on their background, they are likely interested in advancing {field} through applied research.",
        "publication_strength": "Publication record not fully assessed.",
        "potential_funding_areas": ["Horizon Europe", "National research councils", "International foundations"],
        "collaboration_potential": "Likely open to international research collaboration.",
        "consultant_summary": (
            f"{name} works in {field}. "
            "Their profile suggests alignment with major funding programmes. "
            "Recommended for outreach regarding publication support and grant strategy."
        ),
    }
