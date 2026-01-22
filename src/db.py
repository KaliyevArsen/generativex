# Program by Kaliyev.A
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple


STATUSES = ("NEW", "DRAFTED", "SENT_SIMULATED")


@dataclass
class Lead:
    id: int
    company: str
    contact: str
    channel: str
    note: str
    status: str
    created_at: str


@dataclass
class Message:
    id: int
    lead_id: int
    subject: str
    body: str
    created_at: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                contact TEXT NOT NULL,
                channel TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'NEW',
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_lead_id ON messages(lead_id);")


def add_lead(db_path: str, company: str, contact: str, channel: str, note: str) -> int:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO leads(company, contact, channel, note, status, created_at)
            VALUES (?, ?, ?, ?, 'NEW', ?)
            """,
            (company.strip(), contact.strip(), channel.strip(), note.strip(), now),
        )
        return int(cur.lastrowid)


def list_leads(db_path: str, limit: int = 20) -> List[Lead]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, company, contact, channel, note, status, created_at
            FROM leads
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [Lead(**dict(r)) for r in rows]


def get_lead(db_path: str, lead_id: int) -> Optional[Lead]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, company, contact, channel, note, status, created_at
            FROM leads
            WHERE id = ?
            """,
            (lead_id,),
        ).fetchone()
    return Lead(**dict(row)) if row else None


def update_lead_status(db_path: str, lead_id: int, status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with _connect(db_path) as conn:
        conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))


def save_message(db_path: str, lead_id: int, subject: str, body: str) -> int:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO messages(lead_id, subject, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (lead_id, subject.strip(), body.strip(), now),
        )
        return int(cur.lastrowid)


def get_last_message_for_lead(db_path: str, lead_id: int) -> Optional[Message]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, lead_id, subject, body, created_at
            FROM messages
            WHERE lead_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (lead_id,),
        ).fetchone()
    return Message(**dict(row)) if row else None


def count_by_status(db_path: str) -> Dict[str, int]:
    result = {s: 0 for s in STATUSES}
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT status, COUNT(*) as cnt
            FROM leads
            GROUP BY status
            """
        ).fetchall()
    for r in rows:
        status = r["status"]
        if status in result:
            result[status] = int(r["cnt"])
    return result
