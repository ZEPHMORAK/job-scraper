"""
database.py — SQLite handler for the SAFE MODE AI REVENUE ENGINE
Tables: leads, messages, replies, deals, daily_stats
"""
import sqlite3
import json
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "engine.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id              TEXT PRIMARY KEY,
            platform        TEXT NOT NULL,
            title           TEXT,
            company         TEXT,
            url             TEXT,
            budget          REAL DEFAULT 0,
            proposals       INTEGER DEFAULT 0,
            client_spend    REAL DEFAULT 0,
            payment_verified INTEGER DEFAULT 0,
            score           INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'new',
            niche           TEXT,
            raw_json        TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id             TEXT NOT NULL,
            type                TEXT NOT NULL,
            content             TEXT,
            status              TEXT DEFAULT 'pending',
            telegram_message_id INTEGER,
            created_at          TEXT DEFAULT (datetime('now')),
            sent_at             TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        );

        CREATE TABLE IF NOT EXISTS replies (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         TEXT,
            message_id      INTEGER,
            content         TEXT,
            classification  TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS deals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id     TEXT,
            value       REAL,
            currency    TEXT DEFAULT 'USD',
            closed_at   TEXT DEFAULT (datetime('now')),
            notes       TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            date                TEXT PRIMARY KEY,
            leads_scraped       INTEGER DEFAULT 0,
            leads_qualified     INTEGER DEFAULT 0,
            messages_sent       INTEGER DEFAULT 0,
            replies_received    INTEGER DEFAULT 0,
            deals_closed        INTEGER DEFAULT 0,
            revenue             REAL DEFAULT 0
        );
        """)
    print("[DB] Initialized engine.db")


# ─── Leads ────────────────────────────────────────────────────────────────────

def upsert_lead(lead: dict) -> bool:
    """Insert a lead. Returns True if new, False if already exists."""
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM leads WHERE id = ?", (lead["id"],)).fetchone()
        if existing:
            return False
        conn.execute("""
            INSERT INTO leads (id, platform, title, company, url, budget, proposals,
                               client_spend, payment_verified, score, status, niche, raw_json)
            VALUES (:id, :platform, :title, :company, :url, :budget, :proposals,
                    :client_spend, :payment_verified, :score, :status, :niche, :raw_json)
        """, {
            "id": lead["id"],
            "platform": lead.get("platform", ""),
            "title": lead.get("title", ""),
            "company": lead.get("company", ""),
            "url": lead.get("url", ""),
            "budget": lead.get("budget", 0),
            "proposals": lead.get("proposals", 0),
            "client_spend": lead.get("client_spend", 0),
            "payment_verified": 1 if lead.get("payment_verified") else 0,
            "score": lead.get("score", 0),
            "status": "qualified",
            "niche": lead.get("niche", ""),
            "raw_json": json.dumps(lead),
        })
        return True


def update_lead_status(lead_id: str, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))


def get_lead(lead_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None


# ─── Messages ─────────────────────────────────────────────────────────────────

def save_message(lead_id: str, msg_type: str, content: str) -> int:
    """Save a pending message. Returns the message row ID."""
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO messages (lead_id, type, content, status)
            VALUES (?, ?, ?, 'pending')
        """, (lead_id, msg_type, content))
        return cur.lastrowid


def update_message(msg_id: int, status: str, telegram_msg_id: int = None, content: str = None):
    with get_conn() as conn:
        if content:
            conn.execute("UPDATE messages SET content = ? WHERE id = ?", (content, msg_id))
        if telegram_msg_id:
            conn.execute("UPDATE messages SET telegram_message_id = ? WHERE id = ?", (telegram_msg_id, msg_id))
        sent_at = datetime.utcnow().isoformat() if status == "sent" else None
        conn.execute(
            "UPDATE messages SET status = ?, sent_at = ? WHERE id = ?",
            (status, sent_at, msg_id)
        )


def get_message(msg_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
        return dict(row) if row else None


def get_pending_followups() -> list[dict]:
    """Find sent messages with no reply after 2, 4, or 6 days."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT m.*, l.title, l.platform, l.url, l.niche
            FROM messages m
            JOIN leads l ON l.id = m.lead_id
            WHERE m.status = 'sent'
              AND m.type IN ('proposal', 'outreach', 'followup')
              AND m.sent_at IS NOT NULL
              AND julianday('now') - julianday(m.sent_at) IN (2, 4, 6)
              AND NOT EXISTS (
                  SELECT 1 FROM replies r WHERE r.message_id = m.id
              )
        """).fetchall()
        return [dict(r) for r in rows]


# ─── Replies ──────────────────────────────────────────────────────────────────

def save_reply(lead_id: str, message_id: int, content: str, classification: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO replies (lead_id, message_id, content, classification)
            VALUES (?, ?, ?, ?)
        """, (lead_id, message_id, content, classification))
        return cur.lastrowid


# ─── Deals ────────────────────────────────────────────────────────────────────

def save_deal(lead_id: str, value: float, currency: str = "USD", notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO deals (lead_id, value, currency, notes)
            VALUES (?, ?, ?, ?)
        """, (lead_id, value, currency, notes))
        update_lead_status(lead_id, "closed")
        return cur.lastrowid


# ─── Stats ────────────────────────────────────────────────────────────────────

def increment_stat(field: str, amount: float = 1):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO daily_stats (date) VALUES (?) ON CONFLICT(date) DO NOTHING
        """, (today,))
        conn.execute(f"UPDATE daily_stats SET {field} = {field} + ? WHERE date = ?", (amount, today))


def get_stats_summary() -> dict:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                SUM(leads_scraped)    AS total_scraped,
                SUM(leads_qualified)  AS total_qualified,
                SUM(messages_sent)    AS total_sent,
                SUM(replies_received) AS total_replies,
                SUM(deals_closed)     AS total_deals,
                SUM(revenue)          AS total_revenue
            FROM daily_stats
        """).fetchone()
        return dict(rows) if rows else {}
