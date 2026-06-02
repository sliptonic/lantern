"""SQLite store for event/state data: Usage Log + Print-Queue state.

Document content (Sheets) lives in git, NOT here — see app/content.py.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS usage_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT    NOT NULL,
    name       TEXT    NOT NULL,
    activity   TEXT    NOT NULL,
    notes      TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_usage_log_slug ON usage_log(slug);

-- Per-sheet print/overflow state. One row per Sheet.
CREATE TABLE IF NOT EXISTS sheet_state (
    slug                 TEXT PRIMARY KEY,
    dirty                INTEGER NOT NULL DEFAULT 1,   -- needs printing
    overflowing          INTEGER NOT NULL DEFAULT 0,   -- exceeds one Letter Page
    last_printed_commit  TEXT,
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Admin settings (logo path, pin overrides, etc.) as simple key/value.
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Retired machines: hidden from the dashboard + print queue; content/history
-- in git are untouched. Presence of a row = archived.
CREATE TABLE IF NOT EXISTS archived_sheets (
    slug        TEXT PRIMARY KEY,
    archived_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
