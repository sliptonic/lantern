"""Usage Log routes — the frictionless, open (no PIN) walk-up flow,
plus organizer-facing log viewing and CSV export."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from .. import content, state
from ..templating import base_context, render

router = APIRouter()


@router.get("/sheet/{slug}/log", response_class=HTMLResponse)
def log_form(request: Request, slug: str):
    sheet = content.load(slug)
    if sheet is None:
        raise HTTPException(404)
    ctx = base_context(request) | {"slug": slug, "title": sheet.title, "done": False}
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
    ctx = base_context(request) | {"slug": slug, "title": sheet.title, "done": True}
    return render("log_form.html", ctx)


@router.get("/sheet/{slug}/logs", response_class=HTMLResponse)
def log_view(request: Request, slug: str):
    sheet = content.load(slug)
    if sheet is None:
        raise HTTPException(404)
    ctx = base_context(request) | {
        "slug": slug, "title": sheet.title, "entries": state.log_for(slug),
    }
    return render("usage_log.html", ctx)


@router.get("/sheet/{slug}/logs.csv")
def log_csv(slug: str):
    if not content.exists(slug):
        raise HTTPException(404)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "name", "activity", "notes"])
    for e in state.log_for(slug):
        writer.writerow([e["created_at"], e["name"], e["activity"], e["notes"]])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{slug}-usage-log.csv"'},
    )
