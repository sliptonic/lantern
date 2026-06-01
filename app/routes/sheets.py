"""Sheet routes: Dashboard, view, Editor, create, history, Revert, PDF."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from .. import branding, content, pagesize, pdf, qr, sheet_templates, state
from ..config import get_settings
from ..models import Contact, Link, Sheet
from ..security import require_pin
from ..templating import base_context, render

router = APIRouter()


def _links(labels: list[str], urls: list[str]) -> list[Link]:
    """Pair up parallel label/url form fields into Links, dropping blank rows."""
    out = []
    for label, url in zip(labels, urls):
        label, url = label.strip(), url.strip()
        if url:
            out.append(Link(label=label or url, url=url))
    return out


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
    archived = state.archived_slugs()
    active = [s for s in content.list_slugs() if s not in archived]
    ctx = base_context(request) | {
        "sheets": [_gather(s) for s in active],
        "archived": [_gather(s) for s in sorted(archived) if content.exists(s)],
        "queue": state.print_queue(),
        "activity": state.recent_log(15),
    }
    return render("dashboard.html", ctx)


@router.get("/sheet/{slug}/edit", response_class=HTMLResponse)
def edit_form(request: Request, slug: str):
    exists = content.exists(slug)
    sheet = content.load(slug) or Sheet(slug=slug, machine="")
    ctx = base_context(request) | {
        "sheet": sheet, "slug": slug, "is_new": not exists,
        "page": pagesize.resolve(),
        "overflowing": bool(state.get_state(slug).get("overflowing")) if exists else False,
    }
    return render("sheet_edit.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def new_form(request: Request):
    ctx = base_context(request) | {
        "sheet": Sheet(slug="", machine=""), "slug": "", "is_new": True,
        "page": pagesize.resolve(), "overflowing": False,
    }
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
    sw_label: list[str] = Form(default=[]),
    sw_url: list[str] = Form(default=[]),
    man_label: list[str] = Form(default=[]),
    man_url: list[str] = Form(default=[]),
):
    require_pin(pin)
    slug = slug.strip() or content.slugify(machine)
    sheet = Sheet(
        slug=slug,
        machine=machine.strip(),
        contact=Contact(name=contact_name.strip(), info=contact_info.strip()),
        software_links=_links(sw_label, sw_url),
        manual_links=_links(man_label, man_url),
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


@router.post("/sheet/{slug}/archive")
def archive(slug: str, pin: str = Form("")):
    """Retire a machine: hide it from the dashboard and queue. Content/history
    are preserved; logging still works. Reversible via unarchive."""
    require_pin(pin)
    if not content.exists(slug):
        raise HTTPException(404)
    state.archive(slug)
    return RedirectResponse("/", status_code=303)


@router.post("/sheet/{slug}/unarchive")
def unarchive(slug: str, pin: str = Form("")):
    require_pin(pin)
    state.unarchive(slug)
    return RedirectResponse("/", status_code=303)


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
async def sheet_pdf(slug: str, template: str | None = None):
    if not content.exists(slug):
        raise HTTPException(404)
    # ?template= lets Settings preview a specific template without making it active.
    if template and not sheet_templates.exists(template):
        raise HTTPException(404, "Unknown template")
    result = await run_in_threadpool(_render, slug, template)
    return Response(
        content=result.pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{slug}.pdf"'},
    )


def _build_html(slug: str, template: str | None = None) -> str:
    """Render a Sheet through the active (or given) Template to HTML.

    Separated from PDF rendering so the templated output — logo, footer
    branding, layout — is testable without headless Chromium.
    """
    sheet = content.load(slug)
    if sheet is None:
        raise HTTPException(404)
    settings = get_settings()
    repo_url = settings.repo_url
    ctx = {
        "sheet": sheet,
        "body_html": pdf.render_markdown(sheet.body),
        "log_qr": qr.log_qr(slug),
        "edit_qr": qr.edit_qr(slug),
        "logo_data": branding.logo_data_uri(),
        "brand_mark": branding.brand_mark_data_uri(),
        "repo_url": repo_url,
        "repo_url_display": repo_url.split("://", 1)[-1],
        "page": pagesize.resolve(),
    }
    return sheet_templates.render(template or sheet_templates.get_active(), ctx)


def _render(slug: str, template: str | None = None) -> pdf.RenderResult:
    """Build the Template HTML for a Sheet and render it to a PDF."""
    return pdf.render_pdf(_build_html(slug, template), page_format=pagesize.resolve()["format"])
