"""Small persistent key/value settings backed by the SQLite `settings` table.

Used for admin-tunable values that aren't environment config — e.g. the
active sheet Template.
"""
from __future__ import annotations

from .db import connect


def get(key: str, default: str | None = None) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
