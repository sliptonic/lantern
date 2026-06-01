"""Smoke tests for the core tracer-bullet flows (no Chromium/PDF needed).

PDF rendering is exercised separately; here we verify create -> save -> commit,
usage logging, and the print-queue state transitions end to end.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PIN_ENABLED", "0")
    monkeypatch.setenv("BASE_URL", "http://test.local")
    # Import after env is set so settings cache picks up the temp dir.
    from app.config import get_settings
    get_settings.cache_clear()
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_dashboard_empty(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Equipment Info-Sheets" in r.text


def test_create_sheet_and_log_usage(client):
    # Create a Sheet (no PIN since disabled).
    r = client.post("/sheet/save", data={
        "machine": "Laser Cutter", "author": "jane",
        "contact_name": "Jane", "contact_info": "jane@space.org",
        "training_required": "Laser safety", "body": "## How to use\n1. Be careful",
    }, follow_redirects=False)
    assert r.status_code == 303

    # It appears on the dashboard and is queued (Dirty) for printing.
    assert "Laser Cutter" in client.get("/").text
    assert "laser-cutter" in client.get("/queue").text

    # Log usage (open, no PIN).
    r = client.post("/sheet/laser-cutter/log",
                    data={"name": "Bob", "activity": "Cut acrylic", "notes": ""})
    assert r.status_code == 200
    assert "Logged" in r.text

    # Mark printed clears it from the queue.
    client.post("/queue/laser-cutter/printed", follow_redirects=False)
    assert "laser-cutter" not in client.get("/queue").text


def test_history_records_revisions(client):
    client.post("/sheet/save", data={"machine": "Lathe", "author": "a", "body": "v1"})
    client.post("/sheet/save", data={"machine": "Lathe", "slug": "lathe", "author": "b", "body": "v2"})
    r = client.get("/sheet/lathe/history")
    assert r.status_code == 200
    # Two saves -> two revisions.
    assert r.text.count("Revert to this") >= 1
