# SPDX-License-Identifier: AGPL-3.0-or-later
"""Soft-gate helpers for the PIN.

This is NOT authentication — it is a shared wall-posted secret that adds a
little friction to editing/creating Sheets. Toggleable via PIN_ENABLED.
"""
from __future__ import annotations

from fastapi import HTTPException

from .config import get_settings

DEFAULT_PIN = "changeme"


def pin_is_default() -> bool:
    """True when the gate is on but the PIN is still the shipped placeholder."""
    settings = get_settings()
    return settings.pin_enabled and settings.edit_pin == DEFAULT_PIN


def pin_ok(submitted: str | None) -> bool:
    settings = get_settings()
    if not settings.pin_enabled:
        return True
    return (submitted or "") == settings.edit_pin


def require_pin(submitted: str | None) -> None:
    """Raise 403 if the PIN is required and wrong/missing."""
    if not pin_ok(submitted):
        raise HTTPException(status_code=403, detail="Incorrect PIN.")
