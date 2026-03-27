"""
ai/lead_writer.py — Generate niche-specific outreach messages for each lead type
"""
from ai._client import chat
import config

NICHE_PROMPTS = {
    "executive": (
        "You write concise cold outreach to CEOs, founders, and managing directors. "
        "Focus on business automation ROI and time savings. "
        "Under 100 words. Curiosity-based opener, one specific pain point, soft CTA."
    ),
    "law_firm": (
        "You write concise cold outreach to law firms and attorneys. "
        "Focus on client intake automation, document workflows, and billable hour savings. "
        "Under 100 words. Professional tone, specific pain point, soft CTA."
    ),
    "real_estate": (
        "You write concise cold outreach to real estate companies and property developers. "
        "Focus on lead nurturing automation, CRM workflows, and property inquiry chatbots. "
        "Under 100 words. Professional, value-first, soft CTA."
    ),
    "academic": (
        "You write concise cold outreach to professors and PhD researchers. "
        "Focus on research workflow automation, data processing tools, or collaboration systems. "
        "Under 100 words. Respectful, specific to their research area, soft CTA."
    ),
}


def generate_niche_outreach(lead: dict, web_intel: dict) -> str:
    """
    Generate a personalized outreach message based on niche and website gaps.
    """
    niche = lead.get("niche", "executive")
    system_prompt = NICHE_PROMPTS.get(niche, NICHE_PROMPTS["executive"])

    gaps = web_intel.get("signals_missing", [])
    gap_text = ", ".join(gaps) if gaps else "process automation"

    user_msg = (
        f"Lead: {lead.get('title', 'there')}\n"
        f"Niche: {niche.replace('_', ' ')}\n"
        f"Website gaps: {gap_text}\n"
        f"My name: {config.YOUR_NAME}\n"
        f"My offer: {config.YOUR_OFFER}\n\n"
        "Write a short, personalized outreach message for this lead."
    )

    try:
        return chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.75,
            max_tokens=200,
        )
    except Exception as e:
        return (
            f"Hi, I noticed an opportunity to help with {gap_text}. "
            f"I'd love to explore how I can support your team. — {config.YOUR_NAME}"
        )
