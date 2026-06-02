"""Shared Jinja2 template environment."""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from . import baseurl
from .config import get_settings
from .security import pin_is_default

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def base_context(request) -> dict:
    """Context every page needs (base URL, PIN toggle, security banner)."""
    settings = get_settings()
    return {
        "request": request,
        "base_url": baseurl.get(),
        "pin_enabled": settings.pin_enabled,
        "insecure_pin": pin_is_default(),
        "repo_url": settings.repo_url,
        "repo_url_display": settings.repo_url.split("://", 1)[-1],
    }


def render(name: str, ctx: dict):
    """Render a template using the current (request-first) Starlette API."""
    return templates.TemplateResponse(ctx["request"], name, ctx)
