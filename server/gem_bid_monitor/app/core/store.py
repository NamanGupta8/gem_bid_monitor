"""
Tiny SQLite store for matched bids, so /matches has history across restarts
and re-running a check doesn't lose what was already found.

Bids are never hard-deleted, but they ARE marked inactive once a check no
longer finds them among GeM's current results — which covers a bid closing
normally, being cancelled, or getting pulled via a corrigendum. `/matches`
only returns active bids by default, so a cancelled bid stops showing up in
the UI on your very next "Check now" without losing the historical record.
"""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterable, List

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

        # Migrations: add columns added after this DB may have first been created.
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(matched_bids)")}
        if "bid_id" not in existing_cols:
            conn.execute("ALTER TABLE matched_bids ADD COLUMN bid_id TEXT DEFAULT ''")
        if "is_active" not in existing_cols:
            # Anything already in the DB predates this feature — treat it as
            # active until the next check re-evaluates it, rather than
            # silently hiding everyone's existing matches.
            conn.execute("ALTER TABLE matched_bids ADD COLUMN is_active INTEGER DEFAULT 1")
        if "last_checked_at" not in existing_cols:
            conn.execute("ALTER TABLE matched_bids ADD COLUMN last_checked_at TEXT")


def save_matches(matches: List[Dict]) -> List[Dict]:
    """
    Upserts every currently-matching bid: inserts ones never seen before,
    and refreshes mutable fields (dates, quantity, matched keywords) plus
    `is_active=1` / `last_checked_at` for ones already stored — covering a
    corrigendum that changes a bid's details, or a previously-inactive bid
    that has (rarely) reappeared. `first_seen_at` is never touched on update.

    Returns only the ones that are brand new this run (for "NEW MATCH"
    logging) — not the full upserted set.
    """
    now = datetime.now(timezone.utc).isoformat()
    new_matches = []

    with _connect() as conn:
        for m in matches:
            existing = conn.execute(
                "SELECT 1 FROM matched_bids WHERE bid_no = ?", (m["bid_no"],)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE matched_bids
                    SET bid_id = ?, items = ?, quantity = ?, start_date = ?, end_date = ?,
                        ministry = ?, department = ?, matched_keywords = ?,
                        is_active = 1, last_checked_at = ?
                    WHERE bid_no = ?
                    """,
                    (
                        m.get("bid_id", ""),
                        m["items"],
                        str(m.get("quantity", "")),
                        m.get("start_date", ""),
                        m.get("end_date", ""),
                        m.get("ministry", ""),
                        m.get("department", ""),
                        json.dumps(m.get("matched_keywords", [])),
                        now,
                        m["bid_no"],
                    ),
                )
                continue

            conn.execute(
                """
                INSERT INTO matched_bids
                    (bid_no, bid_id, items, quantity, start_date, end_date,
                     ministry, department, matched_keywords, is_active, last_checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
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
                    now,
                ),
            )
            new_matches.append(m)

    return new_matches


def deactivate_stale(current_bid_nos: Iterable[str]) -> List[str]:
    """
    Marks any currently-active stored bid NOT in `current_bid_nos` as
    inactive — i.e. GeM's fresh results no longer include it, so it closed,
    got cancelled, or dropped out for some other reason. Returns the bid_no
    list of everything just deactivated (for logging).
    """
    current = set(current_bid_nos)

    with _connect() as conn:
        active_rows = conn.execute(
            "SELECT bid_no FROM matched_bids WHERE is_active = 1"
        ).fetchall()
        stale = [row["bid_no"] for row in active_rows if row["bid_no"] not in current]

        if stale:
            placeholders = ",".join("?" for _ in stale)
            conn.execute(
                f"UPDATE matched_bids SET is_active = 0 WHERE bid_no IN ({placeholders})",
                stale,
            )

    return stale


def all_matches(only_active: bool = True) -> List[Dict]:
    query = "SELECT * FROM matched_bids"
    if only_active:
        query += " WHERE is_active = 1"
    query += " ORDER BY first_seen_at DESC"

    with _connect() as conn:
        rows = conn.execute(query).fetchall()

    results = []
    for r in rows:
        row = dict(r)
        row["matched_keywords"] = json.loads(row.get("matched_keywords") or "[]")
        results.append(row)
    return results