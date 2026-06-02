# Lantern — Architecture

Lantern is a single FastAPI container that serves printable, branded, single-page
Info-Sheets. Phones reach it over the LAN with no app and no account: scan a
sheet's QR codes to log use or edit it. Edits are versioned in git; changed
sheets enter a print queue.

This document covers the architecture, data model, and HTTP API. For usage and
configuration, see the [README](README.md).

## Overview

```
                      ┌──────────────────────────────────────────────┐
  phone / browser     │             FastAPI app (one container)       │
 ┌───────────┐        │                                               │
 │ scan QR   │──HTTP──▶  routes ─┬─ dashboard / sheet view / log       │
 │ (no app)  │        │          ├─ editor → save (git commit)         │
 └───────────┘        │          ├─ queue / settings / history         │
                      │          ├─ images (upload + serve)            │
                      │          └─ pdf ──▶ headless Chromium (Playwright)
                      │                                               │
                      │   /data ─ content/ (git)   lantern.db (sqlite)│
                      │           images/          templates/  logo.png│
                      └───────────────────────────────────────────────┘
```

- **Two persistence stores, split by data shape.** Versioned *documents*
  (sheets) live as Markdown-frontmatter files in a **git** repo; high-frequency
  *events/state* (usage log, print-queue flags, settings, archive list) live in
  **SQLite**. They never mix.
- **Single process.** Playwright drives a bundled Chromium in the same container
  for PDF rendering. PDF/image bytes are inlined as data URIs (Chromium has no
  server origin to resolve links against).
- All persistent state is under `DATA_DIR` (`/data`), so one volume + snapshots
  backs up everything.

## Stack

- **Web:** FastAPI · Uvicorn · Jinja2 · `python-multipart`
- **Content/versioning:** GitPython · `python-frontmatter` · `markdown-it-py`
- **PDF:** Playwright (headless Chromium) · `pypdf` (page count)
- **QR:** `segno` · **PIN hashing:** `passlib[bcrypt]` · **State:** stdlib `sqlite3`
- **Frontend:** server-rendered Jinja + small vanilla JS (`editor.js`,
  `preview.js`, `pin.js`); no build step.

## Data model

### Sheet — `DATA_DIR/content/sheets/<slug>.md` (git, one commit per save)

YAML frontmatter; the file body is unused (content lives in `rows`):

```yaml
---
slug: laser-cutter          # stable id; drives URLs + QR codes; never changes
title: "Laser cutter"
contact: { name: "Dana Kim", info: "dana@example.org" }
requirements: "Safety course + sign-off"
rows:                       # the two-column body grid
  - { left: "## Cutting\n1. …", kind: none,  value: "" }
  - { left: "### Video",        kind: qr,    value: "https://youtu.be/…" }
  - { left: "Bed layout",       kind: image, value: "<token>.png" }
---
```

A body **row** has a left Markdown column and a right side that is `none`, an
`image` (`value` = token into the image pool), or a `qr` (`value` = URL). Legacy
sheets with a `machine`/`training_required` field or a plain Markdown body are
migrated on load (see `models.Sheet.from_frontmatter`).

### SQLite — `DATA_DIR/lantern.db`

- `usage_log(id, slug, name, activity, notes, created_at)`
- `sheet_state(slug, dirty, overflowing, last_printed_commit, updated_at)`
- `settings(key, value)` — active template, page size, base-URL override, etc.
- `archived_sheets(slug, archived_at)`

### Other `DATA_DIR` paths

- `images/<token>.<ext>` — flat image pool referenced by body rows (not git-versioned).
- `templates/<name>.html` — user-authored sheet templates (shadow built-ins).
- `logo.png` — the uploaded logo.

## Modules (`app/`)

| Module | Responsibility |
|---|---|
| `config.py` | Env-driven settings + derived `DATA_DIR` paths |
| `models.py` | `Sheet`, `BodyRow`, `Contact`, `Link` + frontmatter (de)serialization |
| `content.py` | Git-backed sheet store: list/load/save/history/revert |
| `db.py` / `state.py` | SQLite schema + queries (usage log, queue state, archive) |
| `settings_store.py` | Key/value settings over the `settings` table |
| `sheet_templates.py` | Built-in + user templates; sandboxed Jinja render of a sheet |
| `pagesize.py` | Letter/A4 geometry + active page size |
| `baseurl.py` | Active base URL (QR/link root): persisted override → env default |
| `images.py` | Image pool: save, serve path, data-URI |
| `branding.py` | Uploaded-logo + brand-mark data URIs |
| `qr.py` | Log/Edit/arbitrary-URL QR codes (SVG data URIs) |
| `pdf.py` | Markdown render + Playwright HTML→PDF + page count |
| `security.py` | Shared-PIN soft gate |
| `seed.py` | First-run sample sheets |
| `routes/` | `sheets`, `usage`, `queue`, `admin` routers |

## HTTP API

PIN-gated routes require the shared PIN when `PIN_ENABLED=1`.

| Method | Path | Purpose | Gate |
|---|---|---|---|
| GET | `/` | Dashboard: active sheets, queue, recent activity, archived | — |
| GET | `/new` | New-sheet editor (`?start=<sample>` to prefill) | — |
| GET | `/sheet/{slug}/edit` | Editor | — |
| POST | `/sheet/save` | Create/update a sheet (git commit; sets queue/overflow state) | PIN |
| GET | `/sheet/{slug}/pdf` | Rendered PDF (`?template=` to preview a template) | — |
| GET/POST | `/sheet/{slug}/log` | Usage-log form + record | open |
| GET | `/sheet/{slug}/logs` | Usage-log view | — |
| GET | `/sheet/{slug}/logs.csv` | Usage-log CSV export | — |
| GET | `/sheet/{slug}/history` | Revisions | — |
| POST | `/sheet/{slug}/revert` | Revert to a commit | PIN |
| POST | `/sheet/{slug}/archive` · `/unarchive` | Retire / restore a sheet | PIN |
| POST | `/image/upload` | Store a body image, return its token (AJAX) | — |
| GET | `/image/{token}` | Serve a pooled image | — |
| GET/POST | `/queue` · `/queue/{slug}/printed` | Print queue + mark printed | — |
| GET | `/queue/print-all.pdf` | Combined PDF of the whole queue | — |
| POST | `/queue/printed-all` | Mark the whole queue printed | — |
| GET | `/settings` | Settings (logo, template, page size, base URL) | — |
| POST | `/settings` | Save logo + active template + page size + base URL | PIN |
| GET | `/logo` | Serve the uploaded logo | — |
| GET | `/settings/template/new` · `/{name}/edit` | Template editor | — |
| POST | `/settings/template/save` · `/{name}/delete` | Save / delete a custom template | PIN |
| GET | `/healthz` | Health check | — |

QR codes encode `${BASE_URL}/sheet/{slug}/log` and `…/edit`.

## Rendering & the single-page rule

1. The editor live-previews the body grid client-side (`preview.js` +
   `editor.js`) in a page-ratio box and warns on overflow.
2. On save, `pdf.render_pdf` renders the active template to a PDF via Chromium
   and `pypdf` counts pages.
3. More than one page → `overflowing=1`: the sheet is kept out of the print
   queue and flagged in the editor. Otherwise `dirty=1` and it enters the queue.

Sheets render through a **selectable template** (`sheet_templates`): built-ins
ship in `app/templates/sheets/`; user templates persist in `DATA_DIR/templates/`
and shadow built-ins of the same name. Rendering uses a Jinja
`SandboxedEnvironment`.

## Deployment

- Image: `python:3.12-slim-bookworm` + `git` + `playwright install --with-deps
  chromium`. Runs `uvicorn app.main:app` on port 8080.
- Config via env (`BASE_URL`, `EDIT_PIN`, `PIN_ENABLED`, `PAGE_SIZE`,
  `DATA_DIR`, `REPO_URL`, `SEED_SAMPLES`).
- Mount one volume at `/data`. See `docker-compose.yml` and, for a
  bind-mounted TrueNAS SCALE deploy, `deploy/truenas/` + `docs/truenas.md`.
