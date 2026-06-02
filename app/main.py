"""Lantern FastAPI application entrypoint.

Lantern — printable, always-current info sheets.
Copyright (C) 2026 sliptonic and Lantern contributors.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version. This program is distributed WITHOUT ANY WARRANTY; see the GNU
Affero General Public License (the LICENSE file) for details.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import baseurl
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
    return {"status": "ok", "base_url": baseurl.get()}
