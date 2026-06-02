# SPDX-License-Identifier: AGPL-3.0-or-later
"""Image pool for sheet body rows.

Images embedded in sheet bodies are stored as a flat pool of files in the data
volume (``/data/images/<token>.<ext>``) and referenced by token from a body
Row. They are inlined as data URIs when rendering the PDF (headless Chromium
has no server origin) and served at ``/image/<token>`` for the web UI.

Decoupling images from the sheet slug (a random token, flat pool) means a new,
not-yet-saved sheet can still upload images, and renames don't move files.
"""
from __future__ import annotations

import base64
import re
import secrets
from pathlib import Path

from .branding import _sniff_mime
from .config import get_settings

_TOKEN_RE = re.compile(r"^[a-z0-9]+\.[a-z0-9]+$")
_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif",
        "image/webp": "webp", "image/svg+xml": "svg"}


def _dir() -> Path:
    d = get_settings().images_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def valid_token(token: str) -> bool:
    return bool(token and _TOKEN_RE.match(token))


def save(data: bytes) -> str:
    """Store image bytes, returning the token to reference them by."""
    ext = _EXT.get(_sniff_mime(data), "png")
    token = f"{secrets.token_hex(16)}.{ext}"
    (_dir() / token).write_bytes(data)
    return token


def path_for(token: str) -> Path | None:
    if not valid_token(token):
        return None
    p = _dir() / token
    return p if p.exists() else None


def data_uri(token: str) -> str | None:
    """Inline data URI for an image token, or None if missing/invalid."""
    p = path_for(token)
    if p is None:
        return None
    data = p.read_bytes()
    return f"data:{_sniff_mime(data)};base64," + base64.b64encode(data).decode("ascii")
