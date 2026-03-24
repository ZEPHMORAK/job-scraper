"""
config.py — Load and validate all settings from .env
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        print(f"[CONFIG ERROR] Missing required env var: {key}")
        print(f"  -> Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _list(key: str, default: list = None) -> list:
    raw = os.getenv(key, "")
    if not raw.strip():
        return default or []
    return [item.strip() for item in raw.split(",") if item.strip()]


# ─── Required ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY      = _require("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN  = _require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID    = _require("TELEGRAM_CHAT_ID")

# ─── Optional ─────────────────────────────────────────────────────────────────
EMAIL_HOST          = _optional("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT          = _int("EMAIL_PORT", 587)
EMAIL_USER          = _optional("EMAIL_USER")
EMAIL_PASS          = _optional("EMAIL_PASS")

GOOGLE_MAPS_API_KEY = _optional("GOOGLE_MAPS_API_KEY")
GMAPS_QUERIES       = _list("GMAPS_QUERIES", ["real estate agents Lagos", "business coaches Lagos"])

UPWORK_KEYWORDS     = _list("UPWORK_KEYWORDS", ["web automation", "AI integration", "real estate tech"])
LINKEDIN_KEYWORDS   = _list("LINKEDIN_KEYWORDS", ["automation consultant", "AI developer"])

MIN_BUDGET          = _int("MIN_BUDGET", 20)
MIN_SCORE           = _int("MIN_SCORE", 5)
MODE                = _optional("MODE", "SAFE").upper()
TONE                = _optional("TONE", "professional")
SCHEDULE_HOURS      = _float("SCHEDULE_HOURS", 0.5)
DEBUG_MODE          = _optional("DEBUG_MODE", "false").lower() == "true"

DAILY_UPWORK_LIMIT  = _int("DAILY_UPWORK_LIMIT", 20)
DAILY_LINKEDIN_LIMIT = _int("DAILY_LINKEDIN_LIMIT", 30)
DAILY_EMAIL_LIMIT   = _int("DAILY_EMAIL_LIMIT", 50)

YOUR_NAME           = _optional("YOUR_NAME", "Your Name")
YOUR_OFFER          = _optional("YOUR_OFFER", "I build custom automation systems for coaches and real estate professionals.")
YOUR_PORTFOLIO_URL  = _optional("YOUR_PORTFOLIO_URL", "")
TARGET_PRICING_MIN  = _int("TARGET_PRICING_MIN", 500)
TARGET_PRICING_MAX  = _int("TARGET_PRICING_MAX", 5000)

# ─── Derived ──────────────────────────────────────────────────────────────────
SAFE_MODE           = (MODE == "SAFE")
GMAPS_ENABLED       = bool(GOOGLE_MAPS_API_KEY)
EMAIL_ENABLED       = bool(EMAIL_USER and EMAIL_PASS)

TARGET_NICHES       = ["coaches", "consultants", "real estate", "property", "coaching"]
