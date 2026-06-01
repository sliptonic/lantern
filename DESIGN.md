# Lantern — Design

Makerspace equipment info-sheet system. Posts printable, branded, single-page
info sheets next to machines. Walk-up users scan QR codes to **log usage** or
**edit the sheet**. Edits are versioned; edited sheets enter a **print queue**.

Hard constraints (from the brief):
- **No app install** — everything works in a phone/desktop browser.
- **No authentication** — soft-gated only (see Trust model).
- **Deploy** as a single Docker container on a TrueNAS Scale server (LAN).
- Output **fits one US Letter page** (8.5×11 in — the brief said "legal" but
  8.5×11 is Letter; Legal is 8.5×14). System **enforces one page**.
- **Uniform branded template** across all sheets.

---

## Resolved decisions

| Area | Decision |
|---|---|
| Trust model | Open wiki, **soft-gated**. Usage logging is frictionless. Editing/creating a sheet requires a name (unverified) + a shared **PIN** posted on the wall. PIN enforcement is a config toggle. |
| Reachability | QR codes encode `${BASE_URL}/...`. **`BASE_URL` is configurable** (env var / config file). Works with a static LAN IP, an mDNS hostname, or a real domain — no code change. |
| Sheet content storage | **One markdown file per sheet** with YAML frontmatter, in a **git repository**. Every save is a commit → history, diff, and revert come free. Human-readable, greppable, survives the app. |
| Events & live state | **SQLite** (single file). Holds usage-log entries and print-queue / sheet state. Easy to query, filter, export to CSV. |
| Print rendering | Markdown → templated HTML (print CSS) → **PDF via headless Chromium (Playwright)**, Letter size. Pixel-accurate and identical across printers. |
| Single-page enforcement | On save, render and count pages. **Warn + live preview** with a visible page boundary; save is **always allowed** (edit never lost), but an overflowing sheet is **flagged and blocked from the print queue** until it fits. |
| Sheet schema | **Structured frontmatter fields + freeform markdown body.** Known fields render into fixed template zones (uniform layout); the procedure/checklist is freeform markdown. |
| Print queue | **Dirty-flag, manual clear.** Any save (that fits) marks the sheet "needs printing." Operator opens the queue on the printer machine, prints the PDF, clicks "mark printed." Tracks last-printed commit so re-edits re-queue. No direct printer integration. |
| Create & index | **Admin dashboard + central index.** Lists all machines with status (needs-printing / overflowing / last-logged), plus the print queue and recent activity. "New sheet" is behind the PIN. Walk-up users still use per-sheet QR codes. |
| Branding | Logo uploaded once via admin settings; applied to every sheet template. |
| Stack | **Python · FastAPI + Jinja + HTMX + small vanilla JS.** Playwright-Python (PDF), GitPython (versioning), stdlib sqlite3, markdown renderer, QR generator, pypdf (page count). |

---

## Architecture

```
                       ┌─────────────────────────────────────────┐
   phone / browser     │            FastAPI app (one container)   │
  ┌───────────┐        │                                          │
  │ scan QR   │──HTTP──▶  routes ─┬─ view / log / edit / history  │
  │ (no app)  │        │          ├─ dashboard / queue / settings │
  └───────────┘        │          └─ pdf  ──▶ Playwright/Chromium │
                       │                                          │
                       │  content/  (git repo)   data/lantern.db │
                       │   <slug>.md (+frontmatter)  (sqlite)      │
                       └──────────────┬─────────────┬─────────────┘
                                      │             │
                                  git history   usage log + queue state
```

- **Two persistence stores, by data shape:** versioned *documents* in git;
  high-frequency *events/state* in SQLite. They never mix.
- Single process; Playwright runs Chromium in the same container.

### Data model

**Sheet file** `content/sheets/<slug>.md`:
```yaml
---
slug: laser-cutter            # stable id; drives URLs + QR codes
machine: "Glowforge Pro"
contact:
  name: "Jane Doe"
  info: "jane@space.org / shop hours"
software_links:  [{label: "...", url: "..."}]
manual_links:    [{label: "...", url: "..."}]
training_required: "Laser safety course + sign-off"
---
## How to use
1. ...checklist (freeform markdown)...
```

**SQLite tables:**
- `usage_log(id, slug, name, activity, notes, created_at)`
- `sheet_state(slug, dirty, overflowing, last_printed_commit, updated_at)`
- `settings(key, value)`  — PIN hash, logo path, PIN-enabled toggle, etc.

### Routes (initial)
| Method | Path | Purpose | Gate |
|---|---|---|---|
| GET | `/` | Dashboard: index + queue + activity | — (admin actions PIN'd) |
| GET/POST | `/sheet/{slug}/log` | Usage log form → record | open |
| GET/POST | `/sheet/{slug}/edit` | Markdown editor → save + commit | PIN |
| GET | `/sheet/{slug}/pdf` | Rendered Letter PDF | — |
| GET | `/sheet/{slug}/history` | Versions; revert to a commit | PIN |
| POST | `/sheet/new` | Create sheet | PIN |
| GET/POST | `/queue` | Print queue; "mark printed" | — |
| GET/POST | `/settings` | Logo, PIN, base URL | PIN |

### QR codes (two per sheet, embedded in the PDF)
- **Log:**  `${BASE_URL}/sheet/{slug}/log`
- **Edit:** `${BASE_URL}/sheet/{slug}/edit`

### Single-page pipeline
1. Editor live-previews client-side (marked.js/EasyMDE) inside a Letter-ratio box.
2. On save: render real PDF via Playwright → count pages with pypdf.
3. `pages > 1` → set `overflowing=true`, keep out of queue, surface a banner.
   Otherwise `dirty=true`, enters queue.

---

## Proposed dependencies
- **Web:** `fastapi`, `uvicorn`, `jinja2`, `python-multipart`
- **Content/versioning:** `GitPython`, `python-frontmatter`, `markdown` (or `markdown-it-py`)
- **PDF:** `playwright` (+ `chromium`), `pypdf`
- **QR:** `segno` (or `qrcode`)
- **State:** stdlib `sqlite3`
- **PIN hashing:** `passlib[bcrypt]`
- **Frontend:** HTMX + a small markdown editor (EasyMDE/marked.js), minimal custom CSS for the template

## Deployment
- Base image `python:3.12-slim-bookworm`; install `git` + `playwright install --with-deps chromium`.
- **Config via env:** `BASE_URL`, `EDIT_PIN` (or set in admin), `PIN_ENABLED`, paths.
- **One named volume** mounted at `/data` holding the `content/` git repo, `lantern.db`, and the uploaded logo → survives container rebuilds; trivially backed up by TrueNAS snapshots.
- `docker-compose.yml` with the volume + port mapping.

---

## Open questions / deferred (not blocking)
- Usage-log **viewing/export** in admin (CSV per machine) — assumed yes, low priority.
- **Archiving/deleting** retired machines (vs. hard delete) — soft-archive likely.
- **Backup**: rely on TrueNAS snapshots of `/data`, or also push the git repo to a remote? (snapshots assumed sufficient.)
- Optional **batch combined PDF** for the print operator (print many at once) — easy later add.
- Photo/image on a sheet (uploaded asset vs. linked) — out of v1 scope unless wanted.

## Build roadmap (suggested slices)
1. Scaffold: FastAPI app, `/data` layout, git-backed content store, SQLite init.
2. Sheet model + create/edit (PIN) + git commit on save.
3. PDF render (Playwright) + Letter template + logo + QR codes.
4. Single-page detection + overflow flag + live preview.
5. Usage log form + recording.
6. Dashboard: index, print queue (dirty-flag/mark-printed), recent activity.
7. History/revert view.
8. Dockerfile + compose + config docs.
