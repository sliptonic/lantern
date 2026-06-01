"""Admin Settings routes: Logo upload, sheet-Template chooser & custom CRUD.

All write actions are PIN-gated (the shared Space PIN).
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import content, sheet_templates
from ..config import get_settings
from ..security import require_pin
from ..templating import base_context, render

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    s = get_settings()
    slugs = content.list_slugs()
    ctx = base_context(request) | {
        "has_logo": s.logo_path.exists(),
        "templates": sheet_templates.listing(),
        "active_template": sheet_templates.get_active(),
        "sample_slug": slugs[0] if slugs else None,
    }
    return render("settings.html", ctx)


@router.post("/settings/logo")
async def upload_logo(pin: str = Form(""), logo: UploadFile = File(...)):
    require_pin(pin)
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logo_path.write_bytes(await logo.read())
    return RedirectResponse("/settings", status_code=303)


# --- Sheet Templates -------------------------------------------------------

@router.post("/settings/template/active")
def set_active_template(pin: str = Form(""), name: str = Form(...)):
    require_pin(pin)
    if not sheet_templates.exists(name):
        raise HTTPException(404, "Unknown template")
    sheet_templates.set_active(name)
    return RedirectResponse("/settings", status_code=303)


@router.get("/settings/template/new", response_class=HTMLResponse)
def new_template_form(request: Request, copy_from: str = "default"):
    base = copy_from if sheet_templates.exists(copy_from) else sheet_templates.DEFAULT_TEMPLATE
    ctx = base_context(request) | {
        "name": "",
        "html": sheet_templates.source(base),
        "is_new": True,
        "origin": "custom",
        "context_vars": sheet_templates.CONTEXT_VARS,
    }
    return render("template_edit.html", ctx)


@router.get("/settings/template/{name}/edit", response_class=HTMLResponse)
def edit_template_form(request: Request, name: str):
    if not sheet_templates.exists(name):
        raise HTTPException(404)
    origin = "custom" if name in sheet_templates.custom_names() else "builtin"
    ctx = base_context(request) | {
        "name": name,
        "html": sheet_templates.source(name),
        "is_new": False,
        # A built-in opened for editing is saved as a custom copy that shadows it.
        "origin": origin,
        "context_vars": sheet_templates.CONTEXT_VARS,
    }
    return render("template_edit.html", ctx)


@router.post("/settings/template/save")
def save_template(pin: str = Form(""), name: str = Form(...), html: str = Form(...)):
    require_pin(pin)
    name = name.strip().lower()
    if not sheet_templates.valid_name(name):
        raise HTTPException(400, "Name must be lowercase letters, digits, and hyphens.")
    sheet_templates.save_custom(name, html)
    return RedirectResponse("/settings", status_code=303)


@router.post("/settings/template/{name}/delete")
def delete_template(name: str, pin: str = Form("")):
    require_pin(pin)
    sheet_templates.delete_custom(name)
    return RedirectResponse("/settings", status_code=303)
