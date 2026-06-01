"""Print Queue routes — the Print Operator's view and Mark Printed action."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import content, state
from ..templating import base_context, render

router = APIRouter()


@router.get("/queue", response_class=HTMLResponse)
def queue(request: Request):
    slugs = state.print_queue()
    rows = [{"slug": s, "machine": (content.load(s).machine if content.load(s) else s)}
            for s in slugs]
    ctx = base_context(request) | {"queue": rows}
    return render("queue.html", ctx)


@router.post("/queue/{slug}/printed")
def mark_printed(slug: str):
    commit = content.current_commit(slug) or ""
    state.mark_printed(slug, commit)
    return RedirectResponse("/queue", status_code=303)
