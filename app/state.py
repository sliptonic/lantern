"""Queries over the SQLite event/state store: Usage Log + Print Queue.

Wraps app/db.py so routes never touch SQL directly.
"""
from __future__ import annotations

from .db import connect


# --- Usage Log -------------------------------------------------------------

def add_log_entry(slug: str, name: str, activity: str, notes: str = "") -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO usage_log (slug, name, activity, notes) VALUES (?, ?, ?, ?)",
            (slug, name.strip(), activity.strip(), notes.strip()),
        )


def recent_log(limit: int = 25, slug: str | None = None) -> list[dict]:
    with connect() as conn:
        if slug:
            rows = conn.execute(
                "SELECT * FROM usage_log WHERE slug = ? ORDER BY id DESC LIMIT ?",
                (slug, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM usage_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def log_for(slug: str) -> list[dict]:
    """Every Log Entry for a sheet, newest first (for the log view + export)."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM usage_log WHERE slug = ? ORDER BY id DESC", (slug,)
        ).fetchall()
    return [dict(r) for r in rows]


def log_count(slug: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM usage_log WHERE slug = ?", (slug,)
        ).fetchone()
    return row["n"]


# --- Sheet / Print-Queue state ---------------------------------------------

def _ensure_row(conn, slug: str) -> None:
    conn.execute("INSERT OR IGNORE INTO sheet_state (slug) VALUES (?)", (slug,))


def mark_saved(slug: str, overflowing: bool) -> None:
    """Record a save: Dirty unless Overflowing (Overflowing is blocked from Queue)."""
    with connect() as conn:
        _ensure_row(conn, slug)
        conn.execute(
            "UPDATE sheet_state SET overflowing = ?, dirty = ?, updated_at = datetime('now') "
            "WHERE slug = ?",
            (1 if overflowing else 0, 0 if overflowing else 1, slug),
        )


def mark_printed(slug: str, commit: str) -> None:
    """Print Operator action: clear Dirty and record the Last-Printed Version."""
    with connect() as conn:
        _ensure_row(conn, slug)
        conn.execute(
            "UPDATE sheet_state SET dirty = 0, last_printed_commit = ?, "
            "updated_at = datetime('now') WHERE slug = ?",
            (commit, slug),
        )


def mark_dirty(slugs) -> None:
    """Flag the given sheets as needing a reprint — used when something global
    (e.g. the Base URL baked into every QR code) changes, invalidating the
    posted copies. Creates a state row if missing; Overflowing sheets stay out
    of the Queue."""
    with connect() as conn:
        for slug in slugs:
            _ensure_row(conn, slug)
            conn.execute(
                "UPDATE sheet_state SET dirty = 1, updated_at = datetime('now') "
                "WHERE slug = ? AND overflowing = 0",
                (slug,),
            )


def get_state(slug: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM sheet_state WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else {"slug": slug, "dirty": 0, "overflowing": 0,
                                  "last_printed_commit": None}


def all_state() -> dict[str, dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sheet_state").fetchall()
    return {r["slug"]: dict(r) for r in rows}


def print_queue() -> list[str]:
    """Slugs that are Dirty, not Overflowing, and not Archived — i.e. need printing."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT slug FROM sheet_state WHERE dirty = 1 AND overflowing = 0 "
            "AND slug NOT IN (SELECT slug FROM archived_sheets) "
            "ORDER BY updated_at DESC"
        ).fetchall()
    return [r["slug"] for r in rows]


# --- Archive (retire) ------------------------------------------------------

def archive(slug: str) -> None:
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO archived_sheets (slug) VALUES (?)", (slug,))


def unarchive(slug: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM archived_sheets WHERE slug = ?", (slug,))


def is_archived(slug: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM archived_sheets WHERE slug = ?", (slug,)
        ).fetchone()
    return row is not None


def archived_slugs() -> set[str]:
    with connect() as conn:
        rows = conn.execute("SELECT slug FROM archived_sheets").fetchall()
    return {r["slug"] for r in rows}
