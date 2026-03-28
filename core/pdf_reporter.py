"""
core/pdf_reporter.py — Generate PDF reports for lead intelligence and researcher profiles
"""
from fpdf import FPDF
import io


def _safe(text) -> str:
    return str(text or "N/A").encode("latin-1", errors="replace").decode("latin-1")


# ── RESEARCHER INTELLIGENCE PDF ───────────────────────────────────────────────

def generate_researcher_pdf(
    researcher: dict,
    profile: dict,
    grants: list,
    matches: list,
    outreach: str,
) -> bytes:
    """Generate a full researcher intelligence profile PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    name        = _safe(researcher.get("title", "Unknown"))
    university  = _safe(researcher.get("company", "Unknown"))
    field       = _safe(profile.get("matched_field", "General Research"))
    score       = researcher.get("score", 0)
    opp_score   = profile.get("field_opportunity_score", 0)

    # ── Header ───────────────────────────────────────────────────────────────
    pdf.set_fill_color(20, 40, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "RESEARCHER INTELLIGENCE PROFILE", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, "Research Consulting Intelligence System", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Identity ─────────────────────────────────────────────────────────────
    _section_header(pdf, "RESEARCHER IDENTITY", (20, 40, 80))
    _row(pdf, "Name",           name)
    _row(pdf, "University",     university)
    _row(pdf, "Department",     _safe(researcher.get("department", "")))
    _row(pdf, "Research Field", field)
    _row(pdf, "Location",       _safe(researcher.get("location", "")))
    _row(pdf, "Email",          _safe(researcher.get("email", "")))
    _row(pdf, "Profile URL",    _safe(researcher.get("url", "")))
    pdf.ln(3)

    # ── Scores ───────────────────────────────────────────────────────────────
    _section_header(pdf, "LEAD SCORING", (20, 40, 80))
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(60, 7, "Lead Score:")
    _score_bar(pdf, score)
    pdf.cell(60, 7, "Field Opportunity Score:")
    _score_bar(pdf, int(opp_score))
    pdf.ln(2)

    from core.researcher_scorer import classify_researcher
    classification = classify_researcher(score)
    pdf.set_font("Helvetica", "B", 11)
    r, g, b = _priority_color(classification)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 8, f"Classification: {classification}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(2)

    # Field data
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Research Field Intelligence:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    _row(pdf, "Est. Global Funding", _safe(profile.get("field_funding", "N/A")))
    _row(pdf, "Growth Trend",        _safe(profile.get("field_growth", "N/A")))
    _row(pdf, "Avg Grant Size",      _safe(profile.get("avg_grant_size", "N/A")))
    pdf.ln(3)

    # ── Research Keywords ─────────────────────────────────────────────────────
    keywords = researcher.get("keywords", [])
    if keywords:
        _section_header(pdf, "RESEARCH KEYWORDS", (20, 40, 80))
        pdf.set_font("Helvetica", "", 9)
        kw_text = "  •  ".join(kw.title() for kw in keywords)
        pdf.multi_cell(0, 6, _safe(kw_text))
        pdf.ln(3)

    # ── Intelligence Profile ─────────────────────────────────────────────────
    _section_header(pdf, "INTELLIGENCE PROFILE", (20, 40, 80))

    background = profile.get("academic_background", "")
    if background:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Academic Background:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _safe(background))
        pdf.ln(2)

    themes = profile.get("top_research_themes", [])
    if themes:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Top Research Themes:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for t in themes:
            pdf.cell(8)
            pdf.cell(0, 5, _safe(f"* {t}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    interests = profile.get("likely_research_interests", "")
    if interests:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Likely Research Interests:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _safe(interests))
        pdf.ln(2)

    funding_areas = profile.get("potential_funding_areas", [])
    if funding_areas:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Potential Funding Areas:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for fa in funding_areas:
            pdf.cell(8)
            pdf.cell(0, 5, _safe(f"* {fa}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    summary = profile.get("consultant_summary", "")
    if summary:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Consultant Summary:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_fill_color(240, 245, 255)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, _safe(summary), fill=True)
    pdf.ln(3)

    # ── Grant Matches ─────────────────────────────────────────────────────────
    if matches:
        _section_header(pdf, "GRANT MATCH RESULTS", (10, 100, 60))
        for m in matches[:5]:
            grant       = m["grant"]
            match_score = m["match_score"]
            priority    = m["priority"]
            reasons     = m.get("reasons", [])[:3]

            pdf.set_font("Helvetica", "B", 10)
            pr, pg, pb = _match_color(priority)
            pdf.set_text_color(pr, pg, pb)
            pdf.cell(0, 7, f"{priority} MATCH — {match_score}%", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(30, 30, 30)

            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, _safe(grant.get("name", "Unknown Grant")), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            _row(pdf, "Funder",   _safe(grant.get("funder", "")))
            _row(pdf, "Amount",   _safe(grant.get("amount", "")))
            _row(pdf, "Deadline", _safe(grant.get("deadline", "")))

            if reasons:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(80, 80, 80)
                for r in reasons:
                    pdf.cell(8)
                    pdf.cell(0, 4, _safe(f"- {r}"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(30, 30, 30)

            pdf.ln(3)

    # ── Outreach Draft ────────────────────────────────────────────────────────
    _section_header(pdf, "RECOMMENDED OUTREACH DRAFT", (20, 40, 80))
    pdf.set_fill_color(245, 247, 255)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, _safe(outreach), fill=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Research Consulting Intelligence System — Confidential", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


# ── LEAD PDF (non-academic) ───────────────────────────────────────────────────

def generate_lead_pdf(lead: dict, web_intel: dict, opportunity: dict, outreach: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    niche    = lead.get("niche", "").replace("_", " ").upper()
    priority = opportunity.get("priority", "LOW")
    title    = _safe(lead.get("title", "Unknown"))

    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, f"{priority} OPPORTUNITY LEAD", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Niche: {niche}  |  AI Lead Intelligence System", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    _section_header(pdf, "IDENTITY")
    _row(pdf, "Name / Title", title)
    _row(pdf, "Niche",        niche.title())
    _row(pdf, "Location",     _safe(lead.get("location", "")))
    _row(pdf, "Organization", _safe(lead.get("company", "")))
    pdf.ln(3)

    _section_header(pdf, "CONTACT DETAILS")
    _row(pdf, "Website",  _safe(lead.get("url", "")))
    _row(pdf, "Email",    _safe(lead.get("email", "")))
    _row(pdf, "LinkedIn", _safe(lead.get("linkedin", "")))
    _row(pdf, "Phone",    _safe(lead.get("phone", "")))
    pdf.ln(3)

    _section_header(pdf, "SCORING")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(55, 8, "Lead Score:")
    _score_bar(pdf, lead.get("score", 0))
    pdf.cell(55, 8, "Opportunity Score:")
    _score_bar(pdf, opportunity.get("opportunity_score", 0))
    r, g, b = _priority_color(priority)
    pdf.set_text_color(r, g, b)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Priority: {priority}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(2)

    if opportunity.get("reasoning"):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Score Breakdown:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for reason in opportunity["reasoning"]:
            pdf.cell(8)
            pdf.cell(0, 5, _safe(f"* {reason}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    _section_header(pdf, "WEBSITE INTELLIGENCE")
    _row_bool(pdf, "Website Accessible",  web_intel.get("accessible"))
    _row_bool(pdf, "Has Chatbot",         web_intel.get("has_chatbot"))
    _row_bool(pdf, "Has Booking System",  web_intel.get("has_booking"))
    _row_bool(pdf, "Has Contact Form",    web_intel.get("has_contact_form"))
    _row_bool(pdf, "Modern Website",      web_intel.get("is_modern"))

    if web_intel.get("signals_missing"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(180, 60, 60)
        pdf.cell(0, 5, "Automation Gaps (Your Opportunities):", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for gap in web_intel["signals_missing"]:
            pdf.cell(8)
            pdf.cell(0, 5, _safe(f"* {gap}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(30, 30, 30)
    pdf.ln(3)

    _section_header(pdf, "DESCRIPTION")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _safe(lead.get("description", "No description.")))
    pdf.ln(3)

    _section_header(pdf, "AI-GENERATED OUTREACH DRAFT")
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, _safe(outreach), fill=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "AI Lead Intelligence System — Confidential", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


# ── Shared Helpers ────────────────────────────────────────────────────────────

def _section_header(pdf: FPDF, title: str, color=(50, 50, 120)):
    r, g, b = color
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(2)


def _row(pdf: FPDF, label: str, value: str):
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(50, 6, f"{label}:")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, value or "N/A")


def _row_bool(pdf: FPDF, label: str, value: bool):
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(55, 6, f"{label}:")
    pdf.set_font("Helvetica", "", 9)
    if value:
        pdf.set_text_color(60, 150, 60)
        pdf.cell(0, 6, "Yes", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(180, 60, 60)
        pdf.cell(0, 6, "No", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)


def _score_bar(pdf: FPDF, score: int):
    for i in range(10):
        pdf.set_fill_color(50, 180, 80) if i < score else pdf.set_fill_color(220, 220, 220)
        pdf.cell(8, 6, "", fill=True, border=1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(12, 6, f" {score}/10", new_x="LMARGIN", new_y="NEXT")


def _priority_color(priority: str) -> tuple:
    return {
        "HIGH": (220, 50, 50), "EXCELLENT": (220, 50, 50),
        "MEDIUM": (230, 160, 30), "STRONG": (60, 150, 60),
        "MODERATE": (230, 160, 30),
    }.get(priority, (80, 80, 80))


def _match_color(priority: str) -> tuple:
    return {
        "EXCELLENT": (20, 120, 60),
        "STRONG": (40, 140, 80),
        "MODERATE": (180, 130, 20),
        "POOR": (160, 60, 60),
    }.get(priority, (80, 80, 80))
