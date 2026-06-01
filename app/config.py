"""Runtime configuration, read from environment (see .env.example).

Terms here follow UBIQUITOUS_LANGUAGE.md: Base URL, Space PIN, etc.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Root address every QR code / absolute link is built from.
    base_url: str
    # Root of all runtime data: content git repo, sqlite db, uploaded logo.
    data_dir: Path
    # Shared wall-posted secret required to edit/create sheets.
    edit_pin: str
    # When False, the PIN gate is bypassed entirely (fully open wiki).
    pin_enabled: bool
    # Project source repo, shown/linked in the printed sheet footer.
    repo_url: str
    # Seed sample sheets on first run (when the content store is empty).
    seed_samples: bool
    host: str
    port: int

    # --- Derived runtime paths ---
    @property
    def content_dir(self) -> Path:
        """Git-backed store of sheet markdown files."""
        return self.data_dir / "content"

    @property
    def sheets_dir(self) -> Path:
        return self.content_dir / "sheets"

    @property
    def templates_dir(self) -> Path:
        """User-created sheet Templates (persisted in the data volume)."""
        return self.data_dir / "templates"

    @property
    def db_path(self) -> Path:
        """SQLite file: usage log + print-queue state."""
        return self.data_dir / "lantern.db"

    @property
    def logo_path(self) -> Path:
        return self.data_dir / "logo.png"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        base_url=os.getenv("BASE_URL", "http://localhost:8080").rstrip("/"),
        data_dir=Path(os.getenv("DATA_DIR", "./data")).resolve(),
        edit_pin=os.getenv("EDIT_PIN", "changeme"),
        pin_enabled=_bool(os.getenv("PIN_ENABLED"), True),
        repo_url=os.getenv("REPO_URL", "https://github.com/sliptonic/lantern").rstrip("/"),
        seed_samples=_bool(os.getenv("SEED_SAMPLES"), True),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
