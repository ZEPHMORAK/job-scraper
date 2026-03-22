# SAFE MODE AI REVENUE ENGINE

Automated AI client acquisition system that finds leads, generates proposals, and routes everything through Telegram for your approval before sending.

## Flow
```
Scrape → Filter → Score → AI Draft → Telegram Approval → Send → Follow-up → Close
```

## Setup

### 1. Install Python
Download from https://python.org (disable VPN first to avoid SSL issues).

### 2. Install dependencies
```
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure
```
copy .env.example .env
```
Open `.env` and fill in:
- `OPENAI_API_KEY` — from platform.openai.com
- `TELEGRAM_BOT_TOKEN` — from @BotFather on Telegram
- `TELEGRAM_CHAT_ID` — your Telegram user/chat ID
- `UPWORK_KEYWORDS` — comma-separated search terms
- `LINKEDIN_KEYWORDS` — comma-separated search terms

Optional:
- Email credentials (for sending outreach directly)
- `GOOGLE_MAPS_API_KEY` (for business lead discovery)

### 4. Run
```
python main.py
```

## Telegram Commands
- `/start` — show help
- `/stats` — view performance stats
- `/log_reply LEAD_ID` — log a client reply → AI generates closing response

## Approval Flow
Every qualified lead arrives in Telegram with:
- Lead details (platform, score, budget, proposals)
- AI-generated proposal/outreach message
- **[✅ Send]** **[✏️ Edit]** **[❌ Reject]** buttons

Nothing is sent without your approval.

## Scoring (1–10, only ≥7 forwarded)
| Signal | Points |
|---|---|
| Budget >$1k | 3 |
| Budget $500–$1k | 2 |
| Budget $100–$500 | 1 |
| Niche match (coaching/real estate) | 2 |
| Urgency signals | 1 |
| Proposals <5 | 2 |
| Proposals 5–10 | 1 |

## Follow-up Sequence
- Day 2: Value-driven insight
- Day 4: Social proof / case study
- Day 6: Final check-in (no pressure)

All follow-ups also require Telegram approval.

## Database
All leads, messages, replies, and deals are stored in `engine.db` (SQLite).
View with any SQLite browser (e.g. DB Browser for SQLite).
