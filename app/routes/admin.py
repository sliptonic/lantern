"""Admin Settings routes: Logo upload and config view (PIN-gated).

Scaffold stub — Logo upload + PIN management land here. See DESIGN.md roadmap.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from ..config import get_settings
from ..security import require_pin
from ..templating import base_context, render

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    s = get_settings()
    ctx = base_context(request) | {"has_logo": s.logo_path.exists()}
    return render("settings.html", ctx)


@router.post("/settings/logo")
async def upload_logo(pin: str = Form(""), logo: UploadFile = File(...)):
    require_pin(pin)
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logo_path.write_bytes(await logo.read())
    return RedirectResponse("/settings", status_code=303)
