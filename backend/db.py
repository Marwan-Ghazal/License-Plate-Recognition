"""SQLite layer for the license plate recognition app.

Schema is created on import via init_db(). The DB file lives at
backend/plates.db by default; override with the LPR_DB_PATH env var.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("LPR_DB_PATH", Path(__file__).parent / "plates.db"))


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the plates table if it doesn't exist. Safe to call repeatedly."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plates (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL UNIQUE,
                plate_text      TEXT,
                image_filename  TEXT NOT NULL,
                timestamp       TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_plates_timestamp ON plates(timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_plates_run_id ON plates(run_id)"
        )


def insert_plate(
    run_id: str,
    plate_text: str | None,
    image_filename: str,
) -> int:
    """Insert a recognition result. Returns the new row id."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO plates (run_id, plate_text, image_filename, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, plate_text, image_filename, timestamp),
        )
        return cur.lastrowid


def get_plate(plate_id: int) -> dict | None:
    """Fetch one plate by id. Returns None if not found."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM plates WHERE id = ?", (plate_id,)
        ).fetchone()
        return dict(row) if row else None


def list_plates(limit: int = 100, offset: int = 0) -> list[dict]:
    """Return recent plates, newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM plates ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
