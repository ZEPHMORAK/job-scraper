"""
telegram/formatter.py — Format lead cards and message previews for Telegram (HTML mode).
"""
from datetime import datetime


def format_lead_card(lead: dict, message: str, msg_id: int) -> str:
    """
    Format a full approval card for Telegram.
    Returns HTML-formatted string ready to send.
    """
    platform = lead.get("platform", "").upper()
    score    = lead.get("score", 0)
    score_bar = _score_bar(score)
    title    = _escape(lead.get("title", "Untitled"))
    company  = lead.get("company", "")
    budget   = lead.get("budget", 0)
    proposals = lead.get("proposals", 0)
    client_spend = lead.get("client_spend", 0)
    pv       = lead.get("payment_verified", False)
    niche    = lead.get("niche", "").title()
    url      = lead.get("url", "")
    msg_type = "Proposal" if lead.get("platform") == "upwork" else "Outreach"

    # Header
    lines = [
        f"🔥 <b>New Lead — {platform}</b>  {score_bar}",
        f"Score: <b>{score}/10</b>",
        "",
    ]

    # Lead details
    if platform == "UPWORK":
        pv_icon = "✅" if pv else "❌"
        lines += [
            f"📋 <b>{title}</b>",
            f"💰 Budget: <b>${budget:,.0f}</b>  |  Proposals: <b>{proposals}</b>",
            f"🏢 Client Spend: <b>${client_spend:,.0f}</b>  Payment Verified: {pv_icon}",
        ]
    elif platform == "LINKEDIN":
        lines += [
            f"📋 <b>{title}</b>",
            f"🏢 Company: <b>{_escape(company)}</b>" if company else "",
        ]
    elif platform == "GMAPS":
        address  = _escape(lead.get("address", ""))
        rating   = lead.get("rating", 0)
        reviews  = lead.get("review_count", 0)
        lines += [
            f"📍 <b>{title}</b>",
            f"📌 {address}",
            f"⭐ {rating} ({reviews:,} reviews)",
        ]

    if niche:
        lines.append(f"🎯 Niche: <b>{niche}</b>")
    if url:
        lines.append(f'🔗 <a href="{url}">View →</a>')
    lines.append("")

    # Message preview
    lines += [
        f"✉️ <b>{msg_type} Draft:</b>",
        "─" * 30,
        _escape(message[:800]) + ("..." if len(message) > 800 else ""),
        "─" * 30,
        "",
        f"<i>Message ID: #{msg_id}</i>",
    ]

    return "\n".join(l for l in lines if l is not None)


def format_run_summary(sources: dict, new_jobs: int, new_leads: int) -> str:
    """
    Format the run summary sent at the start of each scraper run.
    sources = {'upwork': True, 'linkedin': True, 'gmaps': False}
    """
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    status = " | ".join(
        f"{k.title()} {'✅' if v else '❌'}"
        for k, v in sources.items()
    )
    total = new_jobs + new_leads
    if total == 0:
        summary = "No new qualified leads this run."
    else:
        parts = []
        if new_jobs:
            parts.append(f"{new_jobs} job{'s' if new_jobs != 1 else ''}")
        if new_leads:
            parts.append(f"{new_leads} business lead{'s' if new_leads != 1 else ''}")
        summary = "New items: " + " + ".join(parts)

    return (
        f"<b>🤖 Scraper Run — {now}</b>\n"
        f"{status}\n"
        f"{summary}"
    )


def format_followup_card(lead: dict, message: str, msg_id: int, day: int) -> str:
    title = _escape(lead.get("title", "Untitled"))
    platform = lead.get("platform", "").upper()
    return (
        f"⏰ <b>Follow-up Day {day} — {platform}</b>\n\n"
        f"📋 <b>{title}</b>\n\n"
        f"✉️ <b>Draft:</b>\n"
        f"{'─' * 30}\n"
        f"{_escape(message[:600])}\n"
        f"{'─' * 30}\n\n"
        f"<i>Message ID: #{msg_id}</i>"
    )


def format_reply_card(reply_text: str, classification: str, closing_msg: str, msg_id: int) -> str:
    icons = {
        "interested": "🟢",
        "curious": "🟡",
        "skeptical": "🟠",
        "price-focused": "💰",
        "cold": "🔴",
    }
    icon = icons.get(classification, "⚪")
    return (
        f"💬 <b>Client Reply Received</b>\n\n"
        f"Classification: {icon} <b>{classification.title()}</b>\n\n"
        f"<b>Their message:</b>\n<i>{_escape(reply_text[:300])}</i>\n\n"
        f"✉️ <b>Suggested Closing Response:</b>\n"
        f"{'─' * 30}\n"
        f"{_escape(closing_msg[:600])}\n"
        f"{'─' * 30}\n\n"
        f"<i>Message ID: #{msg_id}</i>"
    )


def _score_bar(score: int) -> str:
    filled = round(score / 10 * 5)
    return "🟩" * filled + "⬜" * (5 - filled)


def _escape(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
