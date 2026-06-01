"""Shared Jinja2 template environment."""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from .config import get_settings
from .security import pin_is_default

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def base_context(request) -> dict:
    """Context every page needs (base URL, PIN toggle, security banner)."""
    settings = get_settings()
    return {
        "request": request,
        "base_url": settings.base_url,
        "pin_enabled": settings.pin_enabled,
        "insecure_pin": pin_is_default(),
    }


def render(name: str, ctx: dict):
    """Render a template using the current (request-first) Starlette API."""
    return templates.TemplateResponse(ctx["request"], name, ctx)
