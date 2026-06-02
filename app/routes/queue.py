# SPDX-License-Identifier: AGPL-3.0-or-later
"""Print Queue routes — the Print Operator's view, Mark Printed, and the
batch 'print all queued' combined PDF."""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pypdf import PdfReader, PdfWriter
from starlette.concurrency import run_in_threadpool

from .. import content, state
from ..templating import base_context, render
from .sheets import _render

router = APIRouter()


@router.get("/queue", response_class=HTMLResponse)
def queue(request: Request):
    slugs = state.print_queue()
    rows = [{"slug": s, "title": (content.load(s).title if content.load(s) else s)}
            for s in slugs]
    ctx = base_context(request) | {"queue": rows}
    return render("queue.html", ctx)


@router.post("/queue/{slug}/printed")
def mark_printed(slug: str):
    commit = content.current_commit(slug) or ""
    state.mark_printed(slug, commit)
    return RedirectResponse("/queue", status_code=303)


@router.get("/queue/print-all.pdf")
async def print_all():
    """One combined PDF (one page per queued sheet) for printing in a single job."""
    slugs = state.print_queue()
    if not slugs:
        raise HTTPException(404, "The print queue is empty.")
    writer = PdfWriter()
    for slug in slugs:
        result = await run_in_threadpool(_render, slug)
        for page in PdfReader(io.BytesIO(result.pdf)).pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="print-queue.pdf"'},
    )


@router.post("/queue/printed-all")
def mark_all_printed():
    """Clear the whole queue, recording each sheet's current Revision as printed."""
    for slug in state.print_queue():  # snapshot taken before mutation
        state.mark_printed(slug, content.current_commit(slug) or "")
    return RedirectResponse("/queue", status_code=303)
