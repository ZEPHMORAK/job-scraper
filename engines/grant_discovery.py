"""
engines/grant_discovery.py — Grant Intelligence Engine
Maintains a live database of global research funding opportunities.
"""
import time
from core.ddg_search import ddg_search, make_session

# ── Static grant database ───────────────────────────────────────────────────

KNOWN_GRANTS = [
    {
        "id": "grant_horizon_msca",
        "name": "Horizon Europe — Marie Curie Postdoctoral Fellowships",
        "funder": "European Commission",
        "amount": "Up to €260,000",
        "focus": ["All research fields", "International mobility", "Career development"],
        "eligibility": "Postdoctoral researchers, max 8 years post-PhD",
        "collaboration": "Required — must be hosted by EU research institution",
        "deadline": "September annually",
        "url": "https://marie-sklodowska-curie-actions.ec.europa.eu/",
        "fields": ["all fields"],
        "geo": "global",
    },
    {
        "id": "grant_horizon_erc_starting",
        "name": "ERC Starting Grant",
        "funder": "European Research Council",
        "amount": "Up to €1,500,000",
        "focus": ["Frontier research", "Any scientific field"],
        "eligibility": "2–7 years post-PhD, strong research track record",
        "collaboration": "Not required",
        "deadline": "October annually",
        "url": "https://erc.europa.eu/funding/starting-grants",
        "fields": ["all fields"],
        "geo": "global",
    },
    {
        "id": "grant_nih_r01",
        "name": "NIH R01 Research Project Grant",
        "funder": "National Institutes of Health (NIH)",
        "amount": "$250,000–$500,000/year (up to 5 years)",
        "focus": ["Biomedical research", "Clinical research", "Health sciences"],
        "eligibility": "PhD or MD, faculty or equivalent position",
        "collaboration": "Optional",
        "deadline": "Multiple: Feb, Jun, Oct",
        "url": "https://grants.nih.gov/grants/funding/r01.htm",
        "fields": ["Public Health", "Digital Health", "Biotechnology"],
        "geo": "global (US institution preferred)",
    },
    {
        "id": "grant_nsf_career",
        "name": "NSF CAREER Award",
        "funder": "National Science Foundation",
        "amount": "$500,000–$600,000",
        "focus": ["STEM education", "Research integration", "Faculty development"],
        "eligibility": "Untenured assistant professors in first 5 years",
        "collaboration": "Not required",
        "deadline": "July–October (varies by division)",
        "url": "https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=503214",
        "fields": ["Artificial Intelligence", "Cybersecurity", "Education Technology"],
        "geo": "USA",
    },
    {
        "id": "grant_gates_gce",
        "name": "Gates Foundation Grand Challenges Explorations",
        "funder": "Bill & Melinda Gates Foundation",
        "amount": "$100,000 (Phase 1) up to $1,000,000 (Phase 2)",
        "focus": ["Global health", "Agricultural development", "Digital public goods"],
        "eligibility": "Open to all researchers globally",
        "collaboration": "Not required",
        "deadline": "Quarterly rounds",
        "url": "https://gcgh.grandchallenges.org/",
        "fields": ["Public Health", "Agriculture and Food Systems", "Digital Health"],
        "geo": "global",
    },
    {
        "id": "grant_wellcome_discovery",
        "name": "Wellcome Discovery Award",
        "funder": "Wellcome Trust",
        "amount": "Up to £3,000,000",
        "focus": ["Biomedical science", "Health research", "Life sciences"],
        "eligibility": "Established researchers with independent track record",
        "collaboration": "Optional",
        "deadline": "Rolling applications",
        "url": "https://wellcome.org/grant-funding/schemes/discovery-awards",
        "fields": ["Biotechnology", "Public Health", "Digital Health"],
        "geo": "global",
    },
    {
        "id": "grant_worldbank_i2i",
        "name": "World Bank — Ideas for Action (i2i)",
        "funder": "World Bank",
        "amount": "Up to $30,000",
        "focus": ["Development economics", "Poverty reduction", "Sustainability"],
        "eligibility": "Students and researchers worldwide",
        "collaboration": "Optional",
        "deadline": "Annual — November",
        "url": "https://www.worldbank.org/en/programs/ideas4development",
        "fields": ["Agriculture and Food Systems", "Environmental Sustainability"],
        "geo": "global",
    },
    {
        "id": "grant_un_habitat",
        "name": "UN Habitat Research Initiative",
        "funder": "United Nations",
        "amount": "$50,000–$200,000",
        "focus": ["Urban sustainability", "Housing", "Smart cities"],
        "eligibility": "Academic researchers and institutions",
        "collaboration": "Required — multi-country preferred",
        "deadline": "Varies",
        "url": "https://unhabitat.org/",
        "fields": ["Environmental Sustainability", "Energy Transition"],
        "geo": "global",
    },
    {
        "id": "grant_horizon_eic",
        "name": "EIC Pathfinder — Deep Tech Innovation",
        "funder": "European Innovation Council",
        "amount": "Up to €3,000,000",
        "focus": ["Breakthrough technologies", "AI", "Quantum", "Biotech"],
        "eligibility": "Research teams, universities, SMEs",
        "collaboration": "Required — 3+ entities from 3+ countries",
        "deadline": "March annually",
        "url": "https://eic.ec.europa.eu/eic-funding-opportunities/eic-pathfinder_en",
        "fields": ["Artificial Intelligence", "Biotechnology", "Energy Transition"],
        "geo": "global",
    },
    {
        "id": "grant_newton_fund",
        "name": "Newton Fund Research Partnerships",
        "funder": "UK Research and Innovation (UKRI)",
        "amount": "£100,000–£500,000",
        "focus": ["International research collaboration", "Development challenges"],
        "eligibility": "UK and partner country researchers",
        "collaboration": "Required — must include partner country PI",
        "deadline": "Multiple rounds",
        "url": "https://www.newton-gcrf.org/",
        "fields": ["Public Health", "Agriculture and Food Systems", "Climate Science"],
        "geo": "UK + partner countries",
    },
    {
        "id": "grant_tetfund",
        "name": "TETFund National Research Fund (Nigeria)",
        "funder": "Tertiary Education Trust Fund",
        "amount": "₦5M–₦50M",
        "focus": ["Nigerian development", "Applied research", "Technology"],
        "eligibility": "Nigerian university lecturers and researchers",
        "collaboration": "Optional",
        "deadline": "Annual",
        "url": "https://tetfund.gov.ng/",
        "fields": ["Agriculture and Food Systems", "Public Health", "Education Technology"],
        "geo": "Nigeria",
    },
    {
        "id": "grant_carnegie_africa",
        "name": "Carnegie African Diaspora Fellowship",
        "funder": "Carnegie Corporation of New York",
        "amount": "$8,000 per fellowship",
        "focus": ["African higher education", "Research capacity", "Mentorship"],
        "eligibility": "African-born scholars at accredited US/Canadian institutions",
        "collaboration": "Required — partner institution in Africa",
        "deadline": "January annually",
        "url": "https://africandiasporafellowship.org/",
        "fields": ["all fields"],
        "geo": "Africa + USA/Canada",
    },
]


def get_all_grants() -> list[dict]:
    """Return full grant database."""
    return KNOWN_GRANTS


def search_new_grants(session=None, queries: list = None) -> list[dict]:
    """
    Search DDG for recently announced research grants.
    Returns simplified grant dicts (not full profiles).
    """
    if session is None:
        session = make_session()

    queries = queries or [
        "research grant funding 2025 call for proposals",
        "academic research funding open call 2025",
        "NIH NSF grant announcement 2025",
        "Horizon Europe open call 2025",
    ]

    found = []
    seen = set()
    for query in queries:
        results = ddg_search(session, query, max_results=4)
        for r in results:
            url = r["url"]
            if url in seen:
                continue
            seen.add(url)
            found.append({
                "id": "dynamic_" + url[-12:].replace("/", "_"),
                "name": r["title"],
                "funder": "Unknown",
                "amount": "See details",
                "focus": [r["snippet"][:100]],
                "eligibility": "See link",
                "collaboration": "See link",
                "deadline": "See link",
                "url": url,
                "fields": [],
                "geo": "global",
                "dynamic": True,
            })
        time.sleep(1.5)

    return found
