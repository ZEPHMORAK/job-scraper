"""
ai/closer.py — Generate closing messages based on reply classification.
Strategy: Qualify → Value Framing → Price Anchoring → Objection Handling → Close
"""
from ai._client import chat
import config

# Strategy mapping per classification
CLOSING_STRATEGY = {
    "interested":    "qualification + next step (discovery call)",
    "curious":       "value framing + social proof + soft CTA",
    "skeptical":     "credibility + case study + risk reversal",
    "price-focused": "price anchoring + ROI framing + payment options",
    "cold":          "re-engage with new value angle or graceful exit",
}


def generate_closing(reply_text: str, classification: str, lead: dict) -> str:
    """
    Generate a closing response tailored to the client's reply and classification.
    """
    try:
        prompt = _load_prompt("closing")
        strategy = CLOSING_STRATEGY.get(classification, "value framing + CTA")
        context = f"""
Classification: {classification}
Strategy to use: {strategy}

Original lead: {lead.get('title', '')} on {lead.get('platform', '')}
Client reply: {reply_text}

My Name: {config.YOUR_NAME}
My Offer: {config.YOUR_OFFER}
Portfolio: {config.YOUR_PORTFOLIO_URL}
Tone: {config.TONE}
Target Pricing: ${config.TARGET_PRICING_MIN}–${config.TARGET_PRICING_MAX}
""".strip()

        return chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            temperature=0.65,
            max_tokens=400,
        )
    except Exception as e:
        print(f"[AI/Closer] Error: {e}")
        return "Thanks for your reply! I'd love to jump on a quick call to discuss how I can help. When works best for you?"


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert sales closer. Generate a compelling response to move the deal forward."
