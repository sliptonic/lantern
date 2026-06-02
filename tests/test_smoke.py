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
    monkeypatch.setenv("SEED_SAMPLES", "0")  # keep the test store empty/deterministic
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
    client.post("/sheet/save", data={"machine": "Lathe", "author": "a",
                                      "row_left": ["v1"], "row_kind": ["none"], "row_value": [""]})
    client.post("/sheet/save", data={"machine": "Lathe", "slug": "lathe", "author": "b",
                                      "row_left": ["v2"], "row_kind": ["none"], "row_value": [""]})
    r = client.get("/sheet/lathe/history")
    assert r.status_code == 200
    # Two distinct saves -> two revisions.
    assert r.text.count("Revert to this") >= 1


def test_body_rows_image_and_qr(client):
    from app import content, images
    from app.routes.sheets import _build_html

    # Upload an image -> token, servable.
    up = client.post("/image/upload", files={"image": ("d.png", _PNG_1x1, "image/png")})
    assert up.status_code == 200
    token = up.json()["token"]
    assert client.get("/image/" + token).status_code == 200

    # Save a sheet with a QR row and an image row.
    client.post("/sheet/save", data={
        "machine": "CNC", "author": "a",
        "row_left": ["## Setup\n- step one", "See the diagram"],
        "row_kind": ["qr", "image"],
        "row_value": ["https://youtu.be/demo", token],
    })
    sheet = content.load("cnc")
    assert len(sheet.rows) == 2
    assert (sheet.rows[0].kind, sheet.rows[0].value) == ("qr", "https://youtu.be/demo")
    assert (sheet.rows[1].kind, sheet.rows[1].value) == ("image", token)

    html = _build_html("cnc")
    assert "step one" in html                      # left markdown rendered
    assert "youtu.be/demo" in html                 # QR caption
    assert html.count('class="grid-row') >= 2      # two grid rows
    assert images.data_uri(token) in html          # image inlined as data URI


def test_legacy_body_migrates_to_row():
    from app.models import Sheet
    s = Sheet.from_frontmatter({"slug": "x", "machine": "X"}, "hello **world**")
    assert len(s.rows) == 1
    assert s.rows[0].left == "hello **world**" and s.rows[0].kind == "none"


# Minimal valid 1x1 PNG.
_PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f5f0000000049454e44ae426082"
)


def test_logo_embedded_in_sheet_when_present(client):
    from app import branding
    from app.config import get_settings
    from app.routes.sheets import _build_html

    client.post("/sheet/save", data={"machine": "Laser Cutter", "author": "a", "body": "x"})

    # No uploaded logo yet (template-agnostic: assert on the data itself).
    assert branding.logo_data_uri() is None

    # Upload a logo via the unified Settings save -> available as a base64 data URI.
    r = client.post("/settings", files={"logo": ("logo.png", _PNG_1x1, "image/png")})
    assert r.status_code in (200, 303)
    assert get_settings().logo_path.exists()

    uri = branding.logo_data_uri()
    assert uri is not None and uri.startswith("data:image/png;base64,")
    # The active template embeds the uploaded logo (distinct from the brand mark).
    assert uri in _build_html("laser-cutter")


def test_templates_list_switch_and_custom(client):
    from app import sheet_templates
    from app.routes.sheets import _build_html

    client.post("/sheet/save", data={"machine": "Drill Press", "author": "a",
                                      "body": "## Use\n- Be careful"})

    # Both built-ins are available; default is active.
    assert {"default", "classic"} <= set(sheet_templates.all_names())
    assert sheet_templates.get_active() == "default"

    # Default render carries the branded footer (brand mark + repo link) and QRs.
    html = _build_html("drill-press", "default")
    assert "github.com/sliptonic/lantern" in html
    assert "Scan to LOG USE" in html and "Scan to EDIT" in html

    # Classic is a different, valid layout.
    assert "Drill Press" in _build_html("drill-press", "classic")

    # Create a custom template -> listed, renders, can be made active.
    r = client.post("/settings/template/save", data={
        "name": "mine", "html": "<html><body>CUSTOM {{ sheet.machine }}</body></html>"})
    assert r.status_code in (200, 303)
    assert "mine" in sheet_templates.custom_names()
    assert "CUSTOM Drill Press" in _build_html("drill-press", "mine")

    client.post("/settings", data={"active_template": "mine"})
    assert sheet_templates.get_active() == "mine"

    # Deleting the active custom template falls back to default.
    client.post("/settings/template/mine/delete", data={})
    assert "mine" not in sheet_templates.custom_names()
    assert sheet_templates.get_active() == "default"


def test_software_and_manual_links(client):
    from app import content
    from app.routes.sheets import _build_html

    client.post("/sheet/save", data={
        "machine": "CNC Router", "author": "a", "body": "mill",
        "sw_label": ["Fusion 360", ""], "sw_url": ["https://fusion.example", ""],
        "man_label": ["Manual"], "man_url": ["https://manual.example"],
    })

    sheet = content.load("cnc-router")
    # The blank software row is dropped; the filled rows persist to frontmatter.
    assert [(lk.label, lk.url) for lk in sheet.software_links] == [("Fusion 360", "https://fusion.example")]
    assert [(lk.label, lk.url) for lk in sheet.manual_links] == [("Manual", "https://manual.example")]

    # And they render on the sheet.
    html = _build_html("cnc-router")
    assert "fusion.example" in html and "manual.example" in html


def test_new_sheet_from_sample(client):
    # The chooser offers the built-in samples on the New Sheet page.
    page = client.get("/new").text
    assert "Start from" in page and "Prusa MK4 3D Printer" in page

    # Starting from a sample prefills the editor (machine, links, body).
    pre = client.get("/new?start=prusa-mk4-3d-printer").text
    assert "Prusa MK4 3D Printer" in pre
    assert "PrusaSlicer" in pre
    assert "build plate is clean" in pre


def test_unified_settings_save(client):
    from app import branding, pagesize, sheet_templates

    client.post("/settings/template/save",
                data={"name": "alt", "html": "<html>{{ sheet.machine }}</html>"})
    # One save sets logo + active template + page size together.
    r = client.post("/settings", data={"active_template": "alt", "page_size": "a4"},
                    files={"logo": ("l.png", _PNG_1x1, "image/png")})
    assert r.status_code in (200, 303)
    assert sheet_templates.get_active() == "alt"
    assert pagesize.get() == "a4"
    assert branding.logo_data_uri() is not None
    assert client.get("/logo").status_code == 200


def test_page_size_switch(client):
    from app import pagesize
    from app.routes.sheets import _build_html

    client.post("/sheet/save", data={"machine": "Bandsaw", "author": "a", "body": "cut"})

    # Default is US Letter.
    assert pagesize.get() == "letter"
    letter_html = _build_html("bandsaw")
    assert "size: Letter" in letter_html and "8.5in" in letter_html

    # Switch to A4 via Settings -> templates lay out at A4 geometry.
    r = client.post("/settings", data={"page_size": "a4"})
    assert r.status_code in (200, 303)
    assert pagesize.get() == "a4"
    a4_html = _build_html("bandsaw")
    assert "size: A4" in a4_html and "210mm" in a4_html

    # Unknown values fall back to letter.
    pagesize.set("tabloid")
    assert pagesize.get() == "letter"


def test_editor_preview_and_overflow_banner(client):
    from app import state

    client.post("/sheet/save", data={"machine": "Mill", "author": "a", "body": "x"})
    page = client.get("/sheet/mill/edit").text
    assert "/static/preview.js" in page          # live preview wired in
    assert 'class="page-preview"' in page         # the page-ratio preview box

    # When the server marks a sheet overflowing, the editor shows the banner.
    state.mark_saved("mill", overflowing=True)
    assert "too long to fit one page" in client.get("/sheet/mill/edit").text


def test_batch_print_queue(client):
    from app import state

    client.post("/sheet/save", data={"machine": "Drill", "author": "a", "body": "drill"})
    client.post("/sheet/save", data={"machine": "Saw", "author": "a", "body": "saw"})
    assert set(state.print_queue()) == {"drill", "saw"}

    # Mark all printed clears the whole queue in one action.
    r = client.post("/queue/printed-all", follow_redirects=False)
    assert r.status_code == 303
    assert state.print_queue() == []

    # With an empty queue, the combined PDF is a 404 (nothing to print).
    assert client.get("/queue/print-all.pdf").status_code == 404


def test_archive_hides_from_dashboard_and_queue(client):
    from app import state

    client.post("/sheet/save", data={"machine": "Welder", "author": "a", "body": "weld"})
    assert "Welder" in client.get("/").text
    assert "welder" in client.get("/queue").text

    # Archive -> gone from the print queue, content/history preserved.
    r = client.post("/sheet/welder/archive", data={}, follow_redirects=False)
    assert r.status_code == 303
    assert state.is_archived("welder")
    assert "welder" not in client.get("/queue").text
    assert "Archived machines" in client.get("/").text
    assert client.get("/sheet/welder/history").status_code == 200

    # Unarchive -> back in the queue.
    client.post("/sheet/welder/unarchive", data={}, follow_redirects=False)
    assert not state.is_archived("welder")
    assert "welder" in client.get("/queue").text


def test_usage_log_view_and_csv(client):
    client.post("/sheet/save", data={"machine": "Sander", "author": "a", "body": "sand"})
    client.post("/sheet/sander/log", data={"name": "Pat", "activity": "Sanded oak", "notes": "grit 120"})
    client.post("/sheet/sander/log", data={"name": "Lee", "activity": "Sanded pine", "notes": ""})

    # HTML view lists both entries.
    page = client.get("/sheet/sander/logs")
    assert page.status_code == 200
    assert "Pat" in page.text and "Lee" in page.text
    assert "Sanded oak" in page.text and "Sanded pine" in page.text

    # CSV export has a header + a row per entry.
    csv_resp = client.get("/sheet/sander/logs.csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "attachment" in csv_resp.headers["content-disposition"]
    lines = [ln for ln in csv_resp.text.splitlines() if ln.strip()]
    assert lines[0] == "timestamp,name,activity,notes"
    assert len(lines) == 3  # header + 2 entries


def test_default_pin_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BASE_URL", "http://test.local")
    monkeypatch.setenv("SEED_SAMPLES", "0")
    monkeypatch.setenv("PIN_ENABLED", "1")
    monkeypatch.delenv("EDIT_PIN", raising=False)  # falls back to the default
    from app.config import get_settings
    get_settings.cache_clear()
    from app.security import pin_is_default

    assert pin_is_default() is True
    from app.main import app
    with TestClient(app) as c:
        assert "still the default" in c.get("/").text  # banner on every page

    # Setting a real PIN clears the warning.
    monkeypatch.setenv("EDIT_PIN", "s3cret")
    get_settings.cache_clear()
    assert pin_is_default() is False


def test_seed_creates_samples(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BASE_URL", "http://test.local")
    from app.config import get_settings
    get_settings.cache_clear()
    from app import content, seed
    from app.db import init_db

    init_db()
    assert seed.seed_if_empty() == 2
    slugs = content.list_slugs()
    assert "prusa-mk4-3d-printer" in slugs and "epilog-laser-cutter" in slugs
    # Idempotent: it never re-seeds once content exists.
    assert seed.seed_if_empty() == 0
