"""Lantern FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .content import _repo  # ensures content repo exists on startup
from .db import init_db
from .routes import admin, queue, sheets, usage
from .security import DEFAULT_PIN, pin_is_default
from .seed import seed_if_empty

log = logging.getLogger("lantern")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data dir, SQLite schema, and the content git repo if missing.
    init_db()
    _repo()
    # First-run sample sheets so the app isn't empty on a fresh install.
    if get_settings().seed_samples:
        seed_if_empty()
    if pin_is_default():
        log.warning(
            "SECURITY: the PIN is still the default %r. Anyone who can read "
            "the code can edit sheets. Set EDIT_PIN to a real value (or PIN_ENABLED=0 "
            "to intentionally run open).", DEFAULT_PIN,
        )
    yield


app = FastAPI(title="Lantern", version="0.1.0", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

app.include_router(sheets.router)
app.include_router(usage.router)
app.include_router(queue.router)
app.include_router(admin.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "base_url": get_settings().base_url}
