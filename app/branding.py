"""Branding helpers — embedding the makerspace Logo into rendered Sheets.

The Logo is uploaded once via admin Settings and stored at
`DATA_DIR/logo.png`. Because the PDF is rendered from in-memory HTML (no web
server origin), the Logo is inlined as a base64 data URI rather than linked.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from .config import get_settings

# The Lantern project brand mark (vector), shown in the printed sheet footer.
# Distinct from the makerspace Logo (uploaded via Settings, shown in the header).
_BRAND_MARK = Path(__file__).parent / "static" / "lantern.svg"


def _sniff_mime(data: bytes) -> str:
    """Best-effort image type detection from magic bytes (uploads keep a
    `.png` filename regardless of their real format)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.lstrip()[:5].lower() == b"<?xml" or b"<svg" in data[:256].lower():
        return "image/svg+xml"
    return "image/png"


def logo_data_uri() -> str | None:
    """Inline data URI for the uploaded makerspace Logo, or None if unset."""
    path = get_settings().logo_path
    if not path.exists():
        return None
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{_sniff_mime(data)};base64,{encoded}"


@lru_cache
def brand_mark_data_uri() -> str:
    """Inline data URI for the Lantern brand mark (SVG) used in the sheet footer."""
    data = _BRAND_MARK.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
