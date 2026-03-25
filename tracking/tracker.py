"""
tracking/tracker.py — Performance tracking + follow-up scheduler.
Runs daily: finds messages that need follow-up and routes them to Telegram.
"""
import asyncio
from datetime import datetime
import database as db
from ai.followup import generate_followup


def print_stats():
    """Print current performance stats to console."""
    stats = db.get_stats_summary()
    total_sent = stats.get("total_sent") or 0
    total_replies = stats.get("total_replies") or 0
    total_deals = stats.get("total_deals") or 0
    total_revenue = stats.get("total_revenue") or 0

    reply_rate = f"{total_replies / total_sent * 100:.1f}%" if total_sent else "N/A"
    conversion = f"{total_deals / total_sent * 100:.1f}%" if total_sent else "N/A"

    print("\n" + "=" * 45)
    print("  [STATS] SAFE MODE AI REVENUE ENGINE -- STATS")
    print("=" * 45)
    print(f"  Leads scraped:    {stats.get('total_scraped') or 0:>6,}")
    print(f"  Leads qualified:  {stats.get('total_qualified') or 0:>6,}")
    print(f"  Messages sent:    {total_sent:>6,}")
    print(f"  Replies received: {total_replies:>6,}")
    print(f"  Reply rate:       {reply_rate:>6}")
    print(f"  Deals closed:     {total_deals:>6,}")
    print(f"  Revenue:          ${total_revenue:>9,.2f}")
    print(f"  Conversion rate:  {conversion:>6}")
    print("=" * 45 + "\n")


async def check_and_send_followups():
    """
    Check for messages that need a follow-up today (Day 2, 4, or 6 since sent).
    Generate follow-up messages and route to Telegram for approval.
    """
    from tgbot.bot import send_followup_to_telegram

    pending = db.get_pending_followups()
    if not pending:
        print("[Tracker] No follow-ups due today.")
        return

    print(f"[Tracker] {len(pending)} follow-up(s) due today.")

    for msg_record in pending:
        lead_id = msg_record["lead_id"]
        lead = db.get_lead(lead_id)
        if not lead:
            continue

        # Determine which follow-up day this is
        sent_at = msg_record.get("sent_at")
        day = _get_followup_day(sent_at)

        original_msg = msg_record.get("content", "")
        followup_text = generate_followup(lead, original_msg, day)

        new_msg_id = db.save_message(lead_id, "followup", followup_text)
        await send_followup_to_telegram(lead, followup_text, new_msg_id, day)
        print(f"[Tracker] Follow-up Day {day} queued for lead: {lead.get('title', '')[:50]}")


def _get_followup_day(sent_at: str) -> int:
    """Calculate which follow-up day (2, 4, or 6) based on sent_at timestamp."""
    if not sent_at:
        return 2
    try:
        sent = datetime.fromisoformat(sent_at)
        days_ago = (datetime.utcnow() - sent).days
        if days_ago <= 2:
            return 2
        elif days_ago <= 4:
            return 4
        else:
            return 6
    except (ValueError, TypeError):
        return 2


def log_deal(lead_id: str, value: float, currency: str = "USD", notes: str = ""):
    """Log a closed deal and update stats."""
    deal_id = db.save_deal(lead_id, value, currency, notes)
    db.increment_stat("deals_closed")
    db.increment_stat("revenue", value)
    print(f"[Tracker] Deal logged — Lead: {lead_id} | Value: ${value:,.2f} {currency}")
    return deal_id
