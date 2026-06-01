"""Usage Log routes — the frictionless, open (no PIN) walk-up flow."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from .. import content, state
from ..templating import base_context, render

router = APIRouter()


@router.get("/sheet/{slug}/log", response_class=HTMLResponse)
def log_form(request: Request, slug: str):
    sheet = content.load(slug)
    if sheet is None:
        raise HTTPException(404)
    ctx = base_context(request) | {"slug": slug, "machine": sheet.machine, "done": False}
    return render("log_form.html", ctx)


@router.post("/sheet/{slug}/log", response_class=HTMLResponse)
def submit_log(
    request: Request,
    slug: str,
    name: str = Form(...),
    activity: str = Form(...),
    notes: str = Form(""),
):
    if not content.exists(slug):
        raise HTTPException(404)
    state.add_log_entry(slug, name=name, activity=activity, notes=notes)
    sheet = content.load(slug)
    ctx = base_context(request) | {"slug": slug, "machine": sheet.machine, "done": True}
    return render("log_form.html", ctx)
