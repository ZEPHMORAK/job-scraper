"""
ai/classifier.py — Classify incoming client replies using GPT-4o.
Categories: Interested / Curious / Skeptical / Price-focused / Cold
"""
from ai._client import chat

VALID_CLASSES = ["interested", "curious", "skeptical", "price-focused", "cold"]


def classify_reply(reply_text: str) -> str:
    """
    Classify a client reply into one of 5 categories.
    Returns lowercase category string.
    """
    try:
        prompt = _load_prompt("classifier")
        classification = chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Reply:\n{reply_text}"}
            ],
            temperature=0.1,
            max_tokens=20,
        ).lower()
        # Normalize to valid class
        for valid in VALID_CLASSES:
            if valid in classification:
                return valid
        return "curious"  # safe default
    except Exception as e:
        print(f"[AI/Classifier] Error: {e}")
        return "curious"


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Classify the client reply as one of: interested, curious, skeptical, price-focused, cold. Reply with the single word only."
