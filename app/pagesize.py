# SPDX-License-Identifier: AGPL-3.0-or-later
"""Page size (US Letter vs A4) for rendered Info-Sheets.

The active size is a persisted setting (changeable in Settings), defaulting to
the ``PAGE_SIZE`` env var, then US Letter. It drives both the Playwright paper
format and the geometry the Templates lay out against, so a sheet is always
exactly one page of the chosen size.
"""
from __future__ import annotations

from . import settings_store
from .config import get_settings

KEY = "page_size"

# css_size -> @page size keyword; format -> Playwright paper format.
PAGE_SIZES: dict[str, dict[str, str]] = {
    "letter": {"label": "US Letter (8.5 × 11 in)", "css_size": "Letter",
               "format": "Letter", "width": "8.5in", "height": "11in", "aspect": "8.5 / 11"},
    "a4": {"label": "A4 (210 × 297 mm)", "css_size": "A4",
           "format": "A4", "width": "210mm", "height": "297mm", "aspect": "210 / 297"},
}

DEFAULT = "letter"


def _normalize(name: str | None) -> str:
    name = (name or "").strip().lower()
    return name if name in PAGE_SIZES else DEFAULT


def get() -> str:
    """Active page-size key: persisted setting, else env default, else letter."""
    stored = settings_store.get(KEY)
    if stored:
        return _normalize(stored)
    return _normalize(get_settings().page_size)


def set(name: str) -> None:
    settings_store.set(KEY, _normalize(name))


def resolve(name: str | None = None) -> dict[str, str]:
    """Geometry dict (label, css_size, format, width, height) for a size."""
    return PAGE_SIZES[_normalize(name) if name else get()]


def options() -> list[dict[str, str]]:
    active = get()
    return [{"key": k, "label": v["label"], "active": (k == active)}
            for k, v in PAGE_SIZES.items()]
