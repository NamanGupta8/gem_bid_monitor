"""
Tiny SQLite store for matched bids, so /matches has history across restarts
and re-running a check doesn't lose what was already found.
"""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict

from app import config


@contextmanager
def _connect():
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matched_bids (
                bid_no TEXT PRIMARY KEY,
                items TEXT,
                quantity TEXT,
                start_date TEXT,
                end_date TEXT,
                ministry TEXT,
                department TEXT,
                matched_keywords TEXT,
                first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Migration: add bid_id if this DB predates it (e.g. created before
        # the UI added deep-links to GeM's showbidDocument page).
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(matched_bids)")}
        if "bid_id" not in existing_cols:
            conn.execute("ALTER TABLE matched_bids ADD COLUMN bid_id TEXT DEFAULT ''")


def save_matches(matches: List[Dict]) -> List[Dict]:
    """
    Inserts any bid not already stored. Returns only the ones that were
    NEW this run (i.e. not seen in a previous check).
    """
    new_matches = []
    with _connect() as conn:
        for m in matches:
            existing = conn.execute(
                "SELECT 1 FROM matched_bids WHERE bid_no = ?", (m["bid_no"],)
            ).fetchone()
            if existing:
                continue

            conn.execute(
                """
                INSERT INTO matched_bids
                    (bid_no, bid_id, items, quantity, start_date, end_date,
                     ministry, department, matched_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m["bid_no"],
                    m.get("bid_id", ""),
                    m["items"],
                    str(m.get("quantity", "")),
                    m.get("start_date", ""),
                    m.get("end_date", ""),
                    m.get("ministry", ""),
                    m.get("department", ""),
                    json.dumps(m.get("matched_keywords", [])),
                ),
            )
            new_matches.append(m)

    return new_matches


def all_matches() -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM matched_bids ORDER BY first_seen_at DESC"
        ).fetchall()

    results = []
    for r in rows:
        row = dict(r)
        row["matched_keywords"] = json.loads(row.get("matched_keywords") or "[]")
        results.append(row)
    return results
