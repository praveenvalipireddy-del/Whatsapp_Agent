"""Tiny SQLite store for conversation history and pending drafts."""
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).resolve().parent / "data.db"


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wa_id TEXT NOT NULL,       -- vendor phone (E.164, no +)
                role  TEXT NOT NULL,       -- 'vendor' or 'agent'
                body  TEXT NOT NULL,
                ts    REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wa_id TEXT NOT NULL,
                body  TEXT NOT NULL,
                topic TEXT,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending|sent|rejected
                ts    REAL NOT NULL
            );
            """
        )


def add_message(wa_id, role, body):
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (wa_id, role, body, ts) VALUES (?,?,?,?)",
            (wa_id, role, body, time.time()),
        )


def history(wa_id, limit=20):
    with _conn() as c:
        rows = c.execute(
            "SELECT role, body FROM messages WHERE wa_id=? ORDER BY id DESC LIMIT ?",
            (wa_id, limit),
        ).fetchall()
    return [{"role": r["role"], "body": r["body"]} for r in reversed(rows)]


def recent_messages(limit=100):
    """All messages across every number, newest first — for the view page."""
    with _conn() as c:
        rows = c.execute(
            "SELECT wa_id, role, body, ts FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_draft(wa_id, body, topic):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO drafts (wa_id, body, topic, ts) VALUES (?,?,?,?)",
            (wa_id, body, topic, time.time()),
        )
        return cur.lastrowid


def pending_drafts():
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM drafts WHERE status='pending' ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_draft(draft_id):
    with _conn() as c:
        r = c.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    return dict(r) if r else None


def set_draft_status(draft_id, status):
    with _conn() as c:
        c.execute("UPDATE drafts SET status=? WHERE id=?", (status, draft_id))
