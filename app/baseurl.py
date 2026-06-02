# SPDX-License-Identifier: AGPL-3.0-or-later
"""Base URL that every QR code and absolute link is built from.

Defaults to the ``BASE_URL`` env var, but is overridable at runtime in Settings.
This matters because the correct value is the host's LAN IP/hostname plus the
*published* port — which a deployment platform can't auto-derive (notably on
TrueNAS, where the operator picks the host port at install time). A wrong
install-time value would make every printed QR code dead; making it editable
lets the operator fix it without redeploying.
"""
from __future__ import annotations

from . import settings_store
from .config import get_settings

KEY = "base_url"


def _normalize(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def get() -> str:
    """Active base URL: persisted setting if set, else the BASE_URL env value."""
    stored = _normalize(settings_store.get(KEY))
    return stored or get_settings().base_url


def set(value: str) -> None:
    """Persist a base-URL override. An empty value clears it (reverts to env)."""
    settings_store.set(KEY, _normalize(value))
