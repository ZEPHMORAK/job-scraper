"""
main.py — SAFE MODE AI REVENUE ENGINE
Entry point: initializes DB, starts APScheduler, runs scraper immediately,
then starts Telegram bot polling (blocking).

Run with:  python main.py
Stop with: Ctrl+C
"""
import asyncio
import logging
import time
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database as db
from scrapers.upwork import scrape_upwork
from scrapers.indeed import scrape_indeed
from scrapers.gmaps import scrape_gmaps
from filters.lead_filter import filter_leads
from ai.analyzer import analyze_job
from ai.proposal import generate_proposal
from ai.outreach import generate_outreach
from tgbot.bot import build_app, send_lead_to_telegram, send_run_summary
from tracking.tracker import check_and_send_followups, print_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Suppress noisy httpx/telegram logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ─── Core Scrape + Qualify Pipeline ──────────────────────────────────────────

async def scrape_and_qualify():
    """
    Full pipeline run:
    1. Scrape all sources
    2. Filter + score leads
    3. Deduplicate (skip already-seen leads)
    4. Generate AI messages
    5. Send to Telegram for approval
    """
    print(f"\n{'='*50}")
    print(f"  SCRAPER RUN STARTED -- {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*50}")

    # ── Scrape ──
    source_status = {}

    upwork_raw, linkedin_raw, gmaps_raw = [], [], []
    try:
        upwork_raw = scrape_upwork()
        source_status["upwork"] = True
    except Exception as e:
        logger.error(f"Upwork scraper failed: {e}")
        source_status["upwork"] = False

    try:
        linkedin_raw = scrape_indeed()
        source_status["linkedin"] = True
    except Exception as e:
        logger.error(f"Indeed scraper failed: {e}")
        source_status["linkedin"] = False

    try:
        gmaps_raw = scrape_gmaps()
        source_status["gmaps"] = True
    except Exception as e:
        logger.error(f"GMaps scraper failed: {e}")
        source_status["gmaps"] = False

    all_raw = upwork_raw + linkedin_raw + gmaps_raw
    db.increment_stat("leads_scraped", len(all_raw))
    print(f"\n[Main] Total raw leads: {len(all_raw)}")

    # ── Filter + Score ──
    qualified = filter_leads(all_raw)
    db.increment_stat("leads_qualified", len(qualified))

    # ── Deduplicate (skip leads already in DB) ──
    new_leads = []
    for lead in qualified:
        is_new = db.upsert_lead(lead)
        if is_new:
            new_leads.append(lead)

    print(f"[Main] {len(new_leads)} new qualified leads (after dedup)")

    # ── Send run summary to Telegram ──
    new_jobs  = sum(1 for l in new_leads if l.get("type") == "job")
    new_biz   = sum(1 for l in new_leads if l.get("type") == "lead")
    await send_run_summary(source_status, new_jobs, new_biz)

    if not new_leads:
        print("[Main] Nothing new to process this run.")
        return

    # ── Generate AI messages + send to Telegram ──
    for lead in new_leads:
        try:
            platform = lead.get("platform")
            description = lead.get("description", "")
            title = lead.get("title", "")

            # Analyze the job/lead
            analysis = analyze_job(description, title)

            # Generate appropriate message type
            if platform == "upwork":
                message = generate_proposal(lead, analysis)
                msg_type = "proposal"
            else:
                message = generate_outreach(lead, platform)
                msg_type = "outreach"

            # Save to DB as pending
            msg_id = db.save_message(lead["id"], msg_type, message)

            # Send to Telegram for approval
            await send_lead_to_telegram(lead, message, msg_id)

            # Small delay to avoid Telegram rate limits
            await asyncio.sleep(1.5)

        except Exception as e:
            logger.error(f"Failed to process lead '{lead.get('title', '')}': {e}")
            continue

    print(f"[Main] Run complete — {len(new_leads)} leads sent to Telegram for approval.")
    print_stats()


# ─── Follow-up Check ──────────────────────────────────────────────────────────

async def run_followup_check():
    """Daily job: check for messages that need follow-up today."""
    print(f"\n[Main] Running follow-up check — {datetime.now().strftime('%d %b %Y %H:%M')}")
    try:
        await check_and_send_followups()
    except Exception as e:
        logger.error(f"Follow-up check failed: {e}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

async def run():
    # 1. Initialize database
    db.init_db()
    print(f"\n[OK] Database initialized")

    # 2. Print current stats
    print_stats()

    # 3. Build Telegram bot
    app = build_app()
    print(f"[OK] Telegram bot connected")
    print(f"[OK] Mode: {'SAFE (manual approval)' if config.SAFE_MODE else 'AUTO'}")
    print(f"[OK] Schedule: every {config.SCHEDULE_HOURS} hours")
    print(f"[OK] Min budget: ${config.MIN_BUDGET} | Min score: {config.MIN_SCORE}/10")
    print(f"[OK] Upwork keywords: {', '.join(config.UPWORK_KEYWORDS[:3])}...")
    print(f"\n{'='*50}")
    print(f"  SYSTEM RUNNING -- Ctrl+C to stop")
    print(f"{'='*50}\n")

    # 4. Set up APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scrape_and_qualify,
        "interval",
        hours=config.SCHEDULE_HOURS,
        id="scraper",
        next_run_time=datetime.now(),  # run immediately on startup
    )
    scheduler.add_job(
        run_followup_check,
        "cron",
        hour=9,
        minute=0,
        id="followup",
    )
    scheduler.start()

    # 5. Start Telegram bot polling (blocking — runs until Ctrl+C)
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            print("\n[Main] Shutting down...")
        finally:
            scheduler.shutdown(wait=False)
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(run())
