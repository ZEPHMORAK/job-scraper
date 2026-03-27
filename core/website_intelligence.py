"""
core/website_intelligence.py — Analyze websites for automation gaps and signals
"""
import httpx
import urllib3

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
}

CHATBOT_SIGNALS = [
    "intercom", "drift.com", "tidio", "hubspot", "freshchat",
    "livechat", "tawk.to", "crisp.chat", "zendesk", "olark",
    "purechat", "chatbot", "live chat", "livechat",
]

BOOKING_SIGNALS = [
    "calendly", "acuityscheduling", "book a call", "book a meeting",
    "schedule a demo", "appointlet", "book now", "book an appointment",
    "schedule a call", "youcanbook",
]

FORM_SIGNALS = [
    "<form", "contact-form", "contact form", "get in touch",
    "send a message", "inquiry form", "wpcf7", "gravityforms",
]

MODERN_SIGNALS = [
    "__next", "_nuxt", "react", "vue.js", "angular",
    "webpack", "tailwind", "bootstrap/5", "material-ui",
]


def analyze_website(url: str) -> dict:
    """
    Fetch and analyze a website for automation gaps.
    Returns intelligence dict.
    """
    result = {
        "accessible": False,
        "has_chatbot": False,
        "has_booking": False,
        "has_contact_form": False,
        "is_modern": False,
        "automation_gap_score": 0,
        "signals_found": [],
        "signals_missing": [],
    }

    if not url or not url.startswith("http"):
        return result

    # Skip LinkedIn/social pages — no useful intel
    skip_domains = ["linkedin.com", "facebook.com", "twitter.com", "instagram.com",
                    "youtube.com", "duckduckgo.com", "google.com"]
    if any(d in url for d in skip_domains):
        return result

    try:
        with httpx.Client(
            timeout=10,
            verify=False,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            r = client.get(url)
            if r.status_code >= 400:
                return result
            html = r.text.lower()
            result["accessible"] = True
    except Exception:
        return result

    # Check chatbot
    for sig in CHATBOT_SIGNALS:
        if sig in html:
            result["has_chatbot"] = True
            result["signals_found"].append(f"chatbot:{sig}")
            break

    # Check booking
    for sig in BOOKING_SIGNALS:
        if sig in html:
            result["has_booking"] = True
            result["signals_found"].append(f"booking:{sig}")
            break

    # Check contact form
    for sig in FORM_SIGNALS:
        if sig in html:
            result["has_contact_form"] = True
            result["signals_found"].append("contact_form")
            break

    # Check modernity
    for sig in MODERN_SIGNALS:
        if sig in html:
            result["is_modern"] = True
            result["signals_found"].append(f"modern_framework")
            break

    # Calculate automation gap (missing signals = opportunities)
    gap = 0
    if not result["has_chatbot"]:
        gap += 2
        result["signals_missing"].append("No chatbot / live chat")
    if not result["has_booking"]:
        gap += 1
        result["signals_missing"].append("No online booking system")
    if not result["has_contact_form"]:
        gap += 1
        result["signals_missing"].append("No contact form detected")

    result["automation_gap_score"] = gap
    return result
