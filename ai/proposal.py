"""
ai/proposal.py — Generate high-converting Upwork proposals using GPT-4o.
Structure: Hook → Insight → Proof → Low-risk offer → Question
"""
from ai._client import chat
import config


def generate_proposal(lead: dict, analysis: dict) -> str:
    """
    Generate a personalized Upwork proposal for a job lead.
    Returns the proposal text as a string.
    """
    try:
        prompt = _load_prompt("proposal")
        context = _build_context(lead, analysis)
        return chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            temperature=0.7,
            max_tokens=500,
        )
    except Exception as e:
        print(f"[AI/Proposal] Error: {e}")
        return f"Hi, I saw your post about '{lead.get('title', '')}' and I'd love to help. Let's connect!"


def _build_context(lead: dict, analysis: dict) -> str:
    return f"""
Job Title: {lead.get('title', '')}
Budget: ${lead.get('budget', 'Not specified')}
Platform: Upwork

Real Problem: {analysis.get('problem', '')}
Client Goal: {analysis.get('goal', '')}
Ideal Solution: {analysis.get('ideal_solution', '')}
Pain Points: {', '.join(analysis.get('pain_points', []))}

My Name: {config.YOUR_NAME}
My Offer: {config.YOUR_OFFER}
Portfolio: {config.YOUR_PORTFOLIO_URL}
Tone: {config.TONE}
Target Pricing: ${config.TARGET_PRICING_MIN}–${config.TARGET_PRICING_MAX}
""".strip()


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert freelance copywriter who writes high-converting Upwork proposals."
