"""
telegram/bot.py — Telegram approval bot using python-telegram-bot v20+ (async polling).
ALL outgoing messages must be approved here before sending.
Buttons: ✅ Send | ✏️ Edit | ❌ Reject
"""
import asyncio
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

import config
import database as db
from tgbot.formatter import (
    format_lead_card, format_run_summary, format_followup_card, format_reply_card
)

logger = logging.getLogger(__name__)

# Global application reference (set in start_bot)
_app: Application = None

# Track which message IDs are waiting for text edit input
_pending_edit: dict[int, int] = {}   # telegram_user_id → msg_id in DB
_pending_reply: dict[int, str] = {}  # telegram_user_id → lead_id


# ─── Commands ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>SAFE MODE AI REVENUE ENGINE</b>\n\n"
        "I'll send you qualified leads with AI-drafted messages.\n"
        "You approve every message before it's sent.\n\n"
        "Commands:\n"
        "/stats — View performance stats\n"
        "/help — Show this message",
        parse_mode=ParseMode.HTML,
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = db.get_stats_summary()
    reply_rate = (
        f"{stats['total_replies'] / stats['total_sent'] * 100:.1f}%"
        if stats.get("total_sent") else "N/A"
    )
    conversion = (
        f"{stats['total_deals'] / stats['total_sent'] * 100:.1f}%"
        if stats.get("total_sent") else "N/A"
    )
    await update.message.reply_text(
        f"📊 <b>Performance Stats</b>\n\n"
        f"Leads scraped: <b>{stats.get('total_scraped', 0):,}</b>\n"
        f"Leads qualified: <b>{stats.get('total_qualified', 0):,}</b>\n"
        f"Messages sent: <b>{stats.get('total_sent', 0):,}</b>\n"
        f"Replies received: <b>{stats.get('total_replies', 0):,}</b>\n"
        f"Reply rate: <b>{reply_rate}</b>\n"
        f"Deals closed: <b>{stats.get('total_deals', 0):,}</b>\n"
        f"Revenue: <b>${stats.get('total_revenue', 0):,.2f}</b>\n"
        f"Conversion rate: <b>{conversion}</b>",
        parse_mode=ParseMode.HTML,
    )


# ─── Callback Query Handler (button presses) ──────────────────────────────────

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # format: "action:msg_id" or "action:msg_id:lead_id"
    parts = data.split(":")
    if len(parts) < 2:
        return

    action = parts[0]
    msg_id = int(parts[1])
    lead_id = parts[2] if len(parts) > 2 else None

    record = db.get_message(msg_id)
    if not record:
        await query.edit_message_text("⚠️ Message not found in database.")
        return

    if action == "approve":
        await _handle_approve(query, record, msg_id, lead_id)

    elif action == "edit":
        _pending_edit[query.from_user.id] = msg_id
        await query.edit_message_text(
            f"✏️ <b>Edit Mode</b>\n\nReply with your updated message text.\n"
            f"(Message ID: #{msg_id})",
            parse_mode=ParseMode.HTML,
        )

    elif action == "reject":
        db.update_message(msg_id, "rejected")
        db.update_lead_status(record["lead_id"], "rejected")
        await query.edit_message_text(f"❌ Message #{msg_id} rejected and lead archived.")


async def _handle_approve(query, record: dict, msg_id: int, lead_id: str):
    """Mark message as approved → trigger send (email/log)."""
    db.update_message(msg_id, "sent")
    db.increment_stat("messages_sent")

    lead = db.get_lead(record["lead_id"])
    platform = lead["platform"] if lead else "unknown"

    # Email send (if enabled and lead has email context)
    if config.EMAIL_ENABLED and platform in ("gmaps", "linkedin"):
        from mailer.sender import send_email
        try:
            send_email(
                to=f"[Contact via {platform}]",
                subject=f"Re: {lead['title'] if lead else 'Opportunity'}",
                body=record["content"],
            )
        except Exception as e:
            logger.error(f"Email send failed: {e}")

    await query.edit_message_text(
        f"✅ <b>Message #{msg_id} approved and sent!</b>\n\n"
        f"Platform: {platform.upper()}\n"
        f"Type: {record['type'].title()}",
        parse_mode=ParseMode.HTML,
    )


# ─── Text Message Handler (for editing + reply forwarding) ────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Handle edit mode
    if user_id in _pending_edit:
        msg_id = _pending_edit.pop(user_id)
        db.update_message(msg_id, "pending", content=text)
        record = db.get_message(msg_id)
        lead = db.get_lead(record["lead_id"]) if record else None

        # Re-display the updated message with approval buttons
        if lead and record:
            card = format_lead_card(lead, text, msg_id)
            keyboard = _approval_keyboard(msg_id, lead["id"])
            await update.message.reply_text(card, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            await update.message.reply_text(f"✅ Message #{msg_id} updated.")
        return

    # Handle reply forwarding — user pastes a client reply
    if text.startswith("/reply ") or (len(text) > 20 and user_id in _pending_reply):
        lead_id = _pending_reply.pop(user_id, None)
        if not lead_id:
            await update.message.reply_text(
                "To log a client reply, use:\n/log_reply LEAD_ID\nThen paste the reply text."
            )
            return
        await _process_reply(update, lead_id, text)
        return

    await update.message.reply_text(
        "Send /start for help or /stats for performance stats.\n"
        "To log a client reply: /log_reply"
    )


async def cmd_log_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Start reply logging flow: /log_reply"""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: /log_reply LEAD_ID\nThen send the client reply text as the next message."
        )
        return
    lead_id = args[0]
    lead = db.get_lead(lead_id)
    if not lead:
        await update.message.reply_text(f"Lead ID '{lead_id}' not found.")
        return
    _pending_reply[update.effective_user.id] = lead_id
    await update.message.reply_text(
        f"Got it. Now paste the client's reply for:\n<b>{lead['title']}</b>",
        parse_mode=ParseMode.HTML,
    )


async def _process_reply(update: Update, lead_id: str, reply_text: str):
    """Classify reply, generate closing, show for approval."""
    from ai.classifier import classify_reply
    from ai.closer import generate_closing
    from ai.analyzer import _load_prompt  # just for path reference

    lead = db.get_lead(lead_id)
    if not lead:
        await update.message.reply_text("Lead not found.")
        return

    await update.message.reply_text("🧠 Analyzing reply...")

    classification = classify_reply(reply_text)
    closing = generate_closing(reply_text, classification, lead)

    msg_id = db.save_message(lead_id, "closing", closing)
    db.save_reply(lead_id, msg_id, reply_text, classification)
    db.increment_stat("replies_received")

    card = format_reply_card(reply_text, classification, closing, msg_id)
    keyboard = _approval_keyboard(msg_id, lead_id)
    await update.message.reply_text(card, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ─── Keyboard Builder ─────────────────────────────────────────────────────────

def _approval_keyboard(msg_id: int, lead_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Send", callback_data=f"approve:{msg_id}:{lead_id}"),
        InlineKeyboardButton("✏️ Edit", callback_data=f"edit:{msg_id}:{lead_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject:{msg_id}:{lead_id}"),
    ]])


# ─── Send a lead to Telegram (called from scraper.py) ─────────────────────────

async def send_lead_to_telegram(lead: dict, message: str, msg_id: int):
    """Send a lead card with approval buttons to the configured chat."""
    if not _app:
        logger.error("[Telegram] Bot not initialized.")
        return
    card = format_lead_card(lead, message, msg_id)
    keyboard = _approval_keyboard(msg_id, lead["id"])
    try:
        sent = await _app.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=card,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        db.update_message(msg_id, "pending", telegram_msg_id=sent.message_id)
    except Exception as e:
        logger.error(f"[Telegram] Failed to send lead: {e}")


async def send_run_summary(sources: dict, new_jobs: int, new_leads: int):
    if not _app:
        return
    text = format_run_summary(sources, new_jobs, new_leads)
    try:
        await _app.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"[Telegram] Failed to send summary: {e}")


async def send_followup_to_telegram(lead: dict, message: str, msg_id: int, day: int):
    if not _app:
        return
    card = format_followup_card(lead, message, msg_id, day)
    keyboard = _approval_keyboard(msg_id, lead["id"])
    try:
        await _app.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=card,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"[Telegram] Failed to send follow-up: {e}")


# ─── Bot Initialization ───────────────────────────────────────────────────────

def build_app() -> Application:
    global _app
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("log_reply", cmd_log_reply))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    _app = app
    return app
