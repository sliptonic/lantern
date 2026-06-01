"""Sheet routes: Dashboard, view, Editor, create, history, Revert, PDF."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from .. import content, pdf, qr, state
from ..models import Contact, Sheet
from ..security import require_pin
from ..templating import base_context, render, templates

router = APIRouter()


def _gather(slug: str) -> dict:
    """Status row for a Sheet on the Dashboard."""
    sheet = content.load(slug)
    st = state.get_state(slug)
    revs = content.history(slug)
    return {
        "slug": slug,
        "machine": sheet.machine if sheet else slug,
        "dirty": bool(st.get("dirty")),
        "overflowing": bool(st.get("overflowing")),
        "last_logged": (state.recent_log(1, slug) or [{}])[0].get("created_at"),
        "revisions": len(revs),
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    rows = [_gather(s) for s in content.list_slugs()]
    ctx = base_context(request) | {
        "sheets": rows,
        "queue": state.print_queue(),
        "activity": state.recent_log(15),
    }
    return render("dashboard.html", ctx)


@router.get("/sheet/{slug}/edit", response_class=HTMLResponse)
def edit_form(request: Request, slug: str):
    sheet = content.load(slug) or Sheet(slug=slug, machine="")
    ctx = base_context(request) | {"sheet": sheet, "slug": slug, "is_new": not content.exists(slug)}
    return render("sheet_edit.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new_form(request: Request):
    ctx = base_context(request) | {"sheet": Sheet(slug="", machine=""), "slug": "", "is_new": True}
    return render("sheet_edit.html", ctx)


@router.post("/sheet/save")
async def save_sheet(
    request: Request,
    machine: str = Form(...),
    slug: str = Form(""),
    author: str = Form("anonymous"),
    pin: str = Form(""),
    contact_name: str = Form(""),
    contact_info: str = Form(""),
    training_required: str = Form(""),
    body: str = Form(""),
):
    require_pin(pin)
    slug = slug.strip() or content.slugify(machine)
    sheet = Sheet(
        slug=slug,
        machine=machine.strip(),
        contact=Contact(name=contact_name.strip(), info=contact_info.strip()),
        training_required=training_required.strip(),
        body=body,
    )
    content.save(sheet, author=author)

    # Render to detect Overflow, then record print-queue state.
    try:
        result = await run_in_threadpool(_render, slug)
        state.mark_saved(slug, overflowing=result.overflowing)
    except Exception:
        # Rendering unavailable (e.g. Chromium missing in dev) — save still stands.
        state.mark_saved(slug, overflowing=False)

    return RedirectResponse(f"/sheet/{slug}/edit", status_code=303)


@router.get("/sheet/{slug}/history", response_class=HTMLResponse)
def history(request: Request, slug: str):
    if not content.exists(slug):
        raise HTTPException(404)
    ctx = base_context(request) | {"slug": slug, "revisions": content.history(slug)}
    return render("history.html", ctx)


@router.post("/sheet/{slug}/revert")
async def revert(slug: str, commit: str = Form(...), author: str = Form("anonymous"),
                 pin: str = Form("")):
    require_pin(pin)
    content.revert(slug, commit, author=author)
    try:
        result = await run_in_threadpool(_render, slug)
        state.mark_saved(slug, overflowing=result.overflowing)
    except Exception:
        state.mark_saved(slug, overflowing=False)
    return RedirectResponse(f"/sheet/{slug}/history", status_code=303)


@router.get("/sheet/{slug}/pdf")
async def sheet_pdf(slug: str):
    if not content.exists(slug):
        raise HTTPException(404)
    result = await run_in_threadpool(_render, slug)
    return Response(
        content=result.pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{slug}.pdf"'},
    )


def _render(slug: str) -> pdf.RenderResult:
    """Build the Template HTML for a Sheet and render it to a Letter PDF."""
    sheet = content.load(slug)
    if sheet is None:
        raise HTTPException(404)
    html = templates.get_template("sheet_pdf.html").render(
        sheet=sheet,
        body_html=pdf.render_markdown(sheet.body),
        log_qr=qr.log_qr(slug),
        edit_qr=qr.edit_qr(slug),
    )
    return pdf.render_pdf(html)
