"""Render a Sheet to a branded, single Letter Page PDF and detect Overflow.

Pipeline: Sheet (markdown + frontmatter) -> Template HTML -> headless Chromium
(Playwright) -> PDF. Page count is read back with pypdf to enforce the
single-page rule.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from markdown_it import MarkdownIt
from pypdf import PdfReader

_md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")


def render_markdown(text: str) -> str:
    return _md.render(text or "")


@dataclass
class RenderResult:
    pdf: bytes
    pages: int

    @property
    def overflowing(self) -> bool:
        """True when the Sheet exceeds one Letter Page."""
        return self.pages > 1


def render_pdf(html: str, page_format: str = "Letter") -> RenderResult:
    """Render templated HTML to a PDF (Letter or A4) via headless Chromium.

    Uses the sync Playwright API; call from a worker thread under FastAPI
    (e.g. via `starlette.concurrency.run_in_threadpool`) to avoid blocking the
    event loop.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format=page_format,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()

    pages = len(PdfReader(io.BytesIO(pdf_bytes)).pages)
    return RenderResult(pdf=pdf_bytes, pages=pages)
