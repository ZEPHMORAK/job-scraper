"""
main.py — AI LEAD INTELLIGENCE SYSTEM
Pipeline: Hunt → Balance Niches → Contact Discovery → Website Intel →
          Score → Opportunity Detect → Email Report → Telegram Notify

Run: python main.py  |  Stop: Ctrl+C
"""
import sys
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config
import database as db
from scrapers.executives   import scrape_executives
from scrapers.lawfirms     import scrape_lawfirms
from scrapers.real_estate  import scrape_real_estate
from scrapers.academic     import scrape_academic
from scrapers.gmaps        import scrape_gmaps
from core.website_intelligence import analyze_website
from core.opportunity_detector import detect_opportunity
from core.email_reporter   import send_lead_report
from core.email_extractor  import extract_email_from_url
from filters.lead_filter   import filter_leads
from ai.lead_writer        import generate_niche_outreach
from tgbot.bot             import build_app, send_telegram_notification, send_run_summary
from tracking.tracker      import print_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ─── Niche Balancer ──────────────────────────────────────────────────────────

def _balance_niches(*niche_lists, per_niche: int = 15) -> list[dict]:
    """
    Enforce 25% distribution across niches.
    Takes up to `per_niche` leads from each niche.
    """
    balanced = []
    for lst in niche_lists:
        balanced.extend(lst[:per_niche])
    return balanced


# ─── Main Intelligence Pipeline ──────────────────────────────────────────────

async def run_intelligence_pipeline():
    print(f"\n{'='*52}")
    print(f"  AI LEAD ENGINE RUN -- {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*52}")

    source_status = {}

    # ── 1. Lead Hunter Engine (scrape all 4 niches) ──
    exec_leads, law_leads, re_leads, acad_leads = [], [], [], []

    try:
        exec_leads = scrape_executives()
        source_status["executives"] = True
    except Exception as e:
        logger.error(f"Executives scraper failed: {e}")
        source_status["executives"] = False

    try:
        law_leads = scrape_lawfirms()
        source_status["law_firms"] = True
    except Exception as e:
        logger.error(f"LawFirms scraper failed: {e}")
        source_status["law_firms"] = False

    try:
        re_leads = scrape_real_estate()
        source_status["real_estate"] = True
    except Exception as e:
        logger.error(f"RealEstate scraper failed: {e}")
        source_status["real_estate"] = False

    try:
        acad_leads = scrape_academic()
        source_status["academic"] = True
    except Exception as e:
        logger.error(f"Academic scraper failed: {e}")
        source_status["academic"] = False

    # GMaps as bonus real estate leads
    try:
        gmaps_leads = scrape_gmaps()
        re_leads += gmaps_leads
        source_status["gmaps"] = True
    except Exception as e:
        logger.error(f"GMaps scraper failed: {e}")
        source_status["gmaps"] = False

    # ── 2. Niche Rotation Engine (25% each) ──
    all_raw = _balance_niches(exec_leads, law_leads, re_leads, acad_leads, per_niche=15)
    db.increment_stat("leads_scraped", len(all_raw))
    print(f"\n[Pipeline] Raw leads: exec={len(exec_leads)} law={len(law_leads)} "
          f"re={len(re_leads)} acad={len(acad_leads)} | total={len(all_raw)}")

    if not all_raw:
        print("[Pipeline] No raw leads collected this run.")
        await send_run_summary(source_status, 0, 0)
        return

    # ── 3. Contact Discovery Engine ──
    print(f"[Pipeline] Extracting contact info...")
    for lead in all_raw:
        if not lead.get("email") and lead.get("url", "").startswith("http"):
            try:
                email = extract_email_from_url(lead["url"])
                if email:
                    lead["email"] = email
            except Exception:
                pass

    # ── 4. Website / Profile Intelligence Engine ──
    print(f"[Pipeline] Analyzing {len(all_raw)} websites...")
    web_intel_map = {}
    for lead in all_raw:
        url = lead.get("url", "")
        if url and url.startswith("http"):
            web_intel_map[lead["id"]] = analyze_website(url)
        else:
            web_intel_map[lead["id"]] = {}

    # ── 5. Lead Scoring Engine ──
    qualified = filter_leads(all_raw, web_intel_map)
    db.increment_stat("leads_qualified", len(qualified))

    # ── Deduplication ──
    new_leads = []
    for lead in qualified:
        if db.upsert_lead(lead):
            new_leads.append(lead)

    print(f"[Pipeline] {len(new_leads)} new qualified leads after dedup")

    # ── Send run summary ──
    await send_run_summary(source_status, 0, len(new_leads))

    if not new_leads:
        print("[Pipeline] Nothing new this run.")
        return

    # ── 6. Opportunity Detector + 7. Email Report + 8. Telegram Notify ──
    high = medium = low = 0
    for lead in new_leads:
        try:
            intel = web_intel_map.get(lead["id"], {})

            # Detect opportunity
            opportunity = detect_opportunity(lead, intel)
            priority = opportunity["priority"]
            if priority == "HIGH":
                high += 1
            elif priority == "MEDIUM":
                medium += 1
            else:
                low += 1

            # Generate outreach
            outreach = generate_niche_outreach(lead, intel)

            # Save to DB
            msg_id = db.save_message(lead["id"], "outreach", outreach)

            # Email full report
            email_sent = send_lead_report(lead, intel, opportunity, outreach)

            # Telegram brief notification
            await send_telegram_notification(lead, opportunity, outreach, email_sent)

            await asyncio.sleep(1.5)

        except Exception as e:
            logger.error(f"Failed to process lead '{lead.get('title', '')}': {e}")
            continue

    print(f"\n[Pipeline] Done — HIGH:{high} MEDIUM:{medium} LOW:{low}")
    print_stats()


# ─── Entry Point ─────────────────────────────────────────────────────────────

async def run():
    db.init_db()
    print(f"\n[OK] Database initialized")
    print_stats()

    app = build_app()
    print(f"[OK] Telegram bot connected")
    print(f"[OK] Schedule: every {config.SCHEDULE_HOURS}h | Min score: {config.MIN_SCORE}/10")
    print(f"\n{'='*52}")
    print(f"  AI LEAD INTELLIGENCE SYSTEM -- RUNNING")
    print(f"{'='*52}\n")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_intelligence_pipeline,
        "interval",
        hours=config.SCHEDULE_HOURS,
        id="lead_engine",
        next_run_time=datetime.now(),
    )
    scheduler.start()

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        try:
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
