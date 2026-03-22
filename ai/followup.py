"""
ai/followup.py — Generate follow-up messages for leads that haven't replied.
Sequence: Day 2 (value) → Day 4 (social proof) → Day 6 (final check-in)
"""
from ai._client import chat
import config

FOLLOWUP_TONE = {
    2: "value-driven — share a quick insight or tip relevant to their problem",
    4: "social proof — mention a result you got for a similar client (brief case study)",
    6: "final check-in — low-pressure, show you respect their time, leave the door open",
}


def generate_followup(lead: dict, original_message: str, day: int) -> str:
    """
    Generate a follow-up message for day 2, 4, or 6 after no reply.
    """
    try:
        if day not in FOLLOWUP_TONE:
            day = 2
        prompt = _load_prompt("followup")
        context = f"""
Day: {day} (follow-up number {[2,4,6].index(day)+1} of 3)
Tone/Strategy: {FOLLOWUP_TONE[day]}

Lead Title: {lead.get('title', '')}
Platform: {lead.get('platform', '')}
Niche: {lead.get('niche', 'business')}

Original Message Sent:
{original_message[:300]}

My Name: {config.YOUR_NAME}
My Offer: {config.YOUR_OFFER}
Tone: {config.TONE}
""".strip()

        return chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            temperature=0.7,
            max_tokens=300,
        )
    except Exception as e:
        print(f"[AI/Followup] Error: {e}")
        defaults = {
            2: "Hi again! Just wanted to share a quick tip that might be useful for your project. Let me know if you'd like to connect!",
            4: "Following up — I recently helped a similar client achieve great results and thought you might find it valuable. Still happy to chat!",
            6: "Last follow-up — completely understand if the timing isn't right. The door is always open whenever you're ready. Best of luck!",
        }
        return defaults.get(day, "Following up on my previous message — let me know if you'd like to connect!")


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert at writing non-pushy, value-driven follow-up messages that get replies."
