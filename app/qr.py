"""QR code generation for the Log QR and Edit QR.

Both encode `${BASE_URL}/sheet/<slug>/...` so they resolve from any phone on
the local network. Returned as inline SVG data URIs for easy template/PDF use.
"""
from __future__ import annotations

import segno

from . import baseurl


def _data_uri(target: str) -> str:
    qr = segno.make(target, error="m")
    return qr.svg_data_uri(scale=4)


def log_qr(slug: str) -> str:
    """QR that opens the usage-log form for a Sheet."""
    base = baseurl.get()
    return _data_uri(f"{base}/sheet/{slug}/log")


def edit_qr(slug: str) -> str:
    """QR that opens the Editor for a Sheet."""
    base = baseurl.get()
    return _data_uri(f"{base}/sheet/{slug}/edit")


def url_qr(url: str) -> str:
    """QR for an arbitrary URL (e.g. a how-to video) in a body row."""
    return _data_uri(url)
