"""
ai/outreach.py — Generate personalized outreach messages for LinkedIn and email leads.
Curiosity-based, personalized, non-spammy.
"""
from ai._client import chat
import config


def generate_outreach(lead: dict, platform: str = "email") -> str:
    """
    Generate an outreach message for a LinkedIn connection or email cold outreach.
    platform: 'linkedin' | 'email' | 'gmaps'
    """
    try:
        prompt = _load_prompt("outreach")
        context = _build_context(lead, platform)
        return chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            temperature=0.75,
            max_tokens=350,
        )
    except Exception as e:
        print(f"[AI/Outreach] Error: {e}")
        return f"Hi, I came across {lead.get('title', 'your business')} and would love to connect about how I can help."


def _build_context(lead: dict, platform: str) -> str:
    is_gmaps = lead.get("type") == "lead"
    if is_gmaps:
        return f"""
Platform: {platform}
Business Name: {lead.get('title', '')}
Address: {lead.get('address', '')}
Rating: {lead.get('rating', '')} ({lead.get('review_count', 0)} reviews)
Niche: {lead.get('niche', 'business')}

My Name: {config.YOUR_NAME}
My Offer: {config.YOUR_OFFER}
Portfolio: {config.YOUR_PORTFOLIO_URL}
Tone: {config.TONE}
Message Type: Cold outreach to local business — short, curiosity-based, no hard sell
""".strip()
    else:
        return f"""
Platform: {platform}
Job Title: {lead.get('title', '')}
Company: {lead.get('company', '')}
Location: {lead.get('location', 'Remote')}
Niche: {lead.get('niche', 'tech')}

My Name: {config.YOUR_NAME}
My Offer: {config.YOUR_OFFER}
Portfolio: {config.YOUR_PORTFOLIO_URL}
Tone: {config.TONE}
Message Type: LinkedIn connection + brief value proposition (max 300 chars for note)
""".strip()


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert at writing personalized, curiosity-based cold outreach messages."
