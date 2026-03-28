"""
main.py — RESEARCH INTELLIGENCE & GRANT STRATEGY SYSTEM
Pipeline:
  1. Research Field Opportunity Engine
  2. Lead Discovery Engine (researchers)
  3. Lead Scoring Engine
  4. Researcher Intelligence Profile Engine
  5. Grant Intelligence Engine
  6. Grant Match Engine
  7. Telegram Intelligence Alerts (PDF + text)

Run: python main.py  |  Stop: Ctrl+C
"""
import sys
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config
import database as db

# Scrapers
from scrapers.academic       import scrape_academic
from scrapers.google_scholar import scrape_google_scholar
from scrapers.gmaps          import scrape_gmaps
from scrapers.executives     import scrape_executives
from scrapers.lawfirms       import scrape_lawfirms
from scrapers.real_estate    import scrape_real_estate

# Engines
from engines.research_fields   import get_field_opportunity
from engines.grant_discovery   import get_all_grants, search_new_grants
from engines.grant_matcher     import match_grants
from engines.researcher_profile import build_researcher_profile

# Core
from core.researcher_scorer  import score_researcher, classify_researcher
from core.website_intelligence import analyze_website
from core.opportunity_detector import detect_opportunity
from core.email_extractor    import extract_email_from_url
from core.pdf_reporter       import generate_researcher_pdf, generate_lead_pdf

# AI
from ai.lead_writer          import generate_niche_outreach

# Bot
from tgbot.bot import (
    build_app, send_run_summary,
    send_researcher_alert, send_grant_alert, send_match_alert,
    send_telegram_notification,
)
from tracking.tracker import print_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ─── RESEARCH INTELLIGENCE PIPELINE ──────────────────────────────────────────

async def run_research_intelligence():
    print(f"\n{'='*56}")
    print(f"  RESEARCH INTELLIGENCE RUN -- {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*56}")

    source_status = {}

    # ── ENGINE 1: Research Field Opportunity Engine ──────────────────────────
    print("\n[Engine 1] Loading research field funding data...")
    # Field data is static + updated per researcher below

    # ── ENGINE 2: Lead Discovery Engine ─────────────────────────────────────
    print("[Engine 2] Discovering academic researchers...")

    all_researchers = []

    try:
        scholar_leads = scrape_google_scholar()
        all_researchers += scholar_leads
        source_status["google_scholar"] = True
        print(f"  Google Scholar: {len(scholar_leads)} found")
    except Exception as e:
        logger.error(f"Google Scholar scraper failed: {e}")
        source_status["google_scholar"] = False

    try:
        academic_leads = scrape_academic()
        all_researchers += academic_leads
        source_status["university_dirs"] = True
        print(f"  University Dirs: {len(academic_leads)} found")
    except Exception as e:
        logger.error(f"Academic scraper failed: {e}")
        source_status["university_dirs"] = False

    db.increment_stat("leads_scraped", len(all_researchers))
    print(f"\n[Engine 2] Total researchers discovered: {len(all_researchers)}")

    # Contact discovery
    print("[Engine 2] Extracting contact details...")
    for r in all_researchers:
        if not r.get("email") and r.get("url", "").startswith("http"):
            try:
                email = extract_email_from_url(r["url"])
                if email:
                    r["email"] = email
            except Exception:
                pass

    # ── ENGINE 5: Grant Intelligence Engine ──────────────────────────────────
    print("\n[Engine 5] Loading grant database...")
    grants = get_all_grants()
    print(f"  {len(grants)} grants in database")

    # ── ENGINE 3: Lead Scoring Engine ────────────────────────────────────────
    print("\n[Engine 3] Scoring researchers...")
    qualified = []
    for r in all_researchers:
        # Get field opportunity data
        keywords  = r.get("keywords", [])
        field_txt = r.get("description", "")
        field_data = get_field_opportunity(keywords, field_txt)
        r["matched_field"] = field_data["field"]
        r["field_data"] = field_data

        score = score_researcher(r, field_data)
        r["score"] = score

        classification = classify_researcher(score)
        print(f"  {score}/10 [{classification}] {r.get('title', '')[:55]}")

        if score >= config.MIN_SCORE:
            qualified.append(r)

    db.increment_stat("leads_qualified", len(qualified))
    print(f"\n[Engine 3] {len(qualified)} qualified researchers (score >= {config.MIN_SCORE})")

    # Deduplicate
    new_researchers = [r for r in qualified if db.upsert_lead(r)]
    print(f"[Engine 3] {len(new_researchers)} new (after dedup)")

    await send_run_summary(source_status, 0, len(new_researchers))

    if not new_researchers:
        print("[Pipeline] Nothing new this run.")
    else:
        # ── ENGINE 4 + 6 + 7: Profile → Match → Alert ───────────────────────
        print(f"\n[Engine 4] Building researcher profiles + grant matches...")

        for researcher in new_researchers:
            try:
                field_data = researcher.get("field_data", {})

                # Engine 4: Build intelligence profile
                profile = build_researcher_profile(researcher, field_data)

                # Engine 6: Match grants
                matches = match_grants(researcher, grants)
                strong_matches = [m for m in matches if m["match_score"] >= 70]
                all_matches    = [m for m in matches if m["match_score"] >= 50]

                # Generate outreach
                outreach = generate_niche_outreach(researcher, {})

                # Save to DB
                db.save_message(researcher["id"], "outreach", outreach)

                # Engine 7: Generate PDF + send researcher alert
                pdf_bytes = generate_researcher_pdf(
                    researcher, profile, grants, all_matches, outreach
                )
                await send_researcher_alert(researcher, profile, pdf_bytes)

                # Send match alerts for strong matches
                for match in strong_matches[:3]:
                    await send_match_alert(researcher, match)
                    await asyncio.sleep(0.8)

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Failed to process researcher '{researcher.get('title', '')}': {e}")
                continue

    # ── GRANT ALERTS: Send top grants each run ────────────────────────────────
    print(f"\n[Engine 5] Sending top grant opportunities...")
    top_grants = sorted(grants, key=lambda g: len(g.get("focus", [])), reverse=True)[:3]
    for grant in top_grants:
        try:
            await send_grant_alert(grant)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send grant alert: {e}")

    print(f"\n[Pipeline] Research intelligence run complete.")
    print_stats()


# ─── BUSINESS LEADS PIPELINE (parallel) ──────────────────────────────────────

async def run_business_leads():
    """Secondary pipeline for non-academic business leads (exec, law, real estate)."""
    print(f"\n[BizPipeline] Scanning business leads...")

    raw = []
    for fn, name in [
        (scrape_executives,  "Executives"),
        (scrape_lawfirms,    "LawFirms"),
        (scrape_real_estate, "RealEstate"),
    ]:
        try:
            leads = fn()
            raw += leads
            print(f"  {name}: {len(leads)}")
        except Exception as e:
            logger.error(f"{name} failed: {e}")

    gmaps = []
    try:
        gmaps = scrape_gmaps()
        raw += gmaps
        print(f"  GMaps: {len(gmaps)}")
    except Exception as e:
        logger.error(f"GMaps failed: {e}")

    if not raw:
        print("[BizPipeline] No business leads collected.")
        return

    # Website intel + score
    from filters.lead_filter import filter_leads
    web_intel_map = {}
    for lead in raw:
        url = lead.get("url", "")
        if url and url.startswith("http"):
            web_intel_map[lead["id"]] = analyze_website(url)

    qualified = filter_leads(raw, web_intel_map)
    new_leads  = [l for l in qualified if db.upsert_lead(l)]

    for lead in new_leads:
        try:
            intel = web_intel_map.get(lead["id"], {})
            opportunity = detect_opportunity(lead, intel)
            outreach = generate_niche_outreach(lead, intel)
            db.save_message(lead["id"], "outreach", outreach)
            await send_telegram_notification(lead, opportunity, outreach, intel)
            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"Biz lead failed: {e}")

    print(f"[BizPipeline] {len(new_leads)} new business leads sent.")


# ─── COMBINED SCHEDULER JOB ──────────────────────────────────────────────────

async def run_all():
    await run_research_intelligence()
    await run_business_leads()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

async def run():
    db.init_db()
    print("\n[OK] Database initialized")
    print_stats()

    app = build_app()
    print("[OK] Telegram bot connected")
    print(f"[OK] Schedule: every {config.SCHEDULE_HOURS}h")
    print(f"\n{'='*56}")
    print(f"  RESEARCH INTELLIGENCE SYSTEM -- RUNNING")
    print(f"{'='*56}\n")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all,
        "interval",
        hours=config.SCHEDULE_HOURS,
        id="research_engine",
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
