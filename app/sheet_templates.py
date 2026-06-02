"""Multi-template support for rendering Info-Sheets.

A sheet Template is a standalone Jinja HTML document that the sheet context is
rendered through to produce the printable page. Templates come from two places:

- **Built-in**: shipped with the app in ``app/templates/sheets/*.html``.
- **Custom**: authored by admins in Settings, persisted in
  ``DATA_DIR/templates/*.html`` so they survive restarts and can be edited.

A custom template shadows a built-in of the same name. The active Template is
stored in settings (key ``active_template``); the default is ``default``.

Rendering uses a Jinja ``SandboxedEnvironment`` — custom templates are authored
by PIN-gated admins, but sandboxing keeps a stray template from reaching into
the host (no attribute access to dunders, no arbitrary calls).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader, select_autoescape
from jinja2.sandbox import SandboxedEnvironment

from . import settings_store
from .config import get_settings

BUILTIN_DIR = Path(__file__).parent / "templates" / "sheets"
ACTIVE_KEY = "active_template"
DEFAULT_TEMPLATE = "default"

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Context variables a Template may use — surfaced in the editor help.
CONTEXT_VARS = [
    ("sheet.title", "Sheet title"),
    ("sheet.contact.name / sheet.contact.info", "Contact person"),
    ("sheet.requirements", "Requirements / prerequisites text"),
    ("sheet.software_links / sheet.manual_links", "Lists of {label, url}"),
    ("rows", "Body grid rows: each has left_html, kind, image_data, qr_data, url"),
    ("body_html", "Legacy: all rows' left columns joined (mark | safe)"),
    ("logo_data", "Uploaded logo as a data URI (or None)"),
    ("brand_mark", "Lantern brand mark as a data URI"),
    ("log_qr / edit_qr", "QR code data URIs"),
    ("repo_url / repo_url_display", "Project repo link"),
    ("page.css_size / page.width / page.height", "Page size (Letter/A4) + dimensions"),
]


@dataclass
class TemplateInfo:
    name: str
    origin: str  # 'builtin' | 'custom'
    is_active: bool


def _user_dir() -> Path:
    d = get_settings().templates_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def _env() -> SandboxedEnvironment:
    # User dir first so a custom template shadows a built-in of the same name.
    loader = ChoiceLoader([FileSystemLoader(str(_user_dir())), FileSystemLoader(str(BUILTIN_DIR))])
    return SandboxedEnvironment(loader=loader, autoescape=select_autoescape(["html"]))


def valid_name(name: str) -> bool:
    return bool(_NAME_RE.match(name or ""))


def builtin_names() -> list[str]:
    return sorted(p.stem for p in BUILTIN_DIR.glob("*.html"))


def custom_names() -> list[str]:
    return sorted(p.stem for p in _user_dir().glob("*.html"))


def all_names() -> list[str]:
    return sorted(set(builtin_names()) | set(custom_names()))


def exists(name: str) -> bool:
    return name in builtin_names() or name in custom_names()


def get_active() -> str:
    active = settings_store.get(ACTIVE_KEY, DEFAULT_TEMPLATE)
    return active if exists(active) else DEFAULT_TEMPLATE


def set_active(name: str) -> None:
    if not exists(name):
        raise ValueError(f"Unknown template: {name}")
    settings_store.set(ACTIVE_KEY, name)


def listing() -> list[TemplateInfo]:
    active = get_active()
    custom = set(custom_names())
    out = []
    for name in all_names():
        origin = "custom" if name in custom else "builtin"
        out.append(TemplateInfo(name=name, origin=origin, is_active=(name == active)))
    return out


def source(name: str) -> str:
    """The template source text — a custom copy shadows the built-in."""
    custom = _user_dir() / f"{name}.html"
    if custom.exists():
        return custom.read_text()
    builtin = BUILTIN_DIR / f"{name}.html"
    if builtin.exists():
        return builtin.read_text()
    raise FileNotFoundError(name)


def save_custom(name: str, html: str) -> None:
    if not valid_name(name):
        raise ValueError("Template name must be lowercase letters, digits, and hyphens.")
    (_user_dir() / f"{name}.html").write_text(html)


def delete_custom(name: str) -> bool:
    """Delete a custom template. Built-ins cannot be deleted."""
    path = _user_dir() / f"{name}.html"
    if path.exists():
        path.unlink()
        if get_active() == name and not exists(name):
            set_active(DEFAULT_TEMPLATE)
        return True
    return False


def render(name: str, ctx: dict) -> str:
    return _env().get_template(f"{name}.html").render(**ctx)
