<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="app/static/lantern-white.svg">
    <img src="app/static/lantern.svg" alt="Lantern" height="120">
  </picture>
</p>

<h1 align="center">Lantern</h1>

<p align="center"><em>Post a procedure on the wall. Anyone can read it, log that they used it, or fix it — from their phone, no app, no account.</em></p>

---

Lantern makes the one-page reference sheets you tape to a wall: the startup
checklist beside a machine, the cleaning steps in a kitchen, the runbook in a
server closet, the safety notes by a tool. Each sheet has a contact, a
procedure, links, and two QR codes — one to **log that the thing was used**,
one to **fix the sheet**. Every sheet stays **easy to correct**, **fully
versioned**, and **ready to reprint**.

No app to install. No account to create. Walk up, scan, done.

## Why it exists

Posted instructions go stale. The contact leaves, a step changes, a link rots —
and the paper on the wall is now wrong, with no obvious way to fix it. Lantern
turns each sheet into a living document:

- **See it** — a clean, branded, single-page sheet posted where it's needed.
- **Fix it** — spot an error, scan the *edit* QR, correct it in your browser.
  Old versions are never lost.
- **Log it** — scan the *log* QR, type your name and what you did.
- **Reprint it** — corrected sheets land in a print queue for whoever's at the
  printer.

## How people use it

**Someone following the procedure** reads the posted sheet and scans the **Log**
QR to record a quick entry (name · what they did · notes). No login.

**Someone fixing a sheet** scans the **Edit** QR, edits in their browser, enters
the shared **PIN** (posted on the wall), and saves. Every save is a new version
— mistakes are one click to revert.

**Whoever prints** opens the **Print Queue**, sees every sheet that changed
since it was last printed, and prints it (one sheet, or the whole queue at once)
on plain paper.

**Whoever organizes** uses the **Dashboard** to see every sheet's status, create
new ones, and retire old ones.

## What's on a sheet

Each sheet is one page (US Letter or A4) with a uniform, logo-branded layout:

- A title and your logo
- A contact and how to reach them
- Requirements / prerequisites
- Links (software, manuals, anything)
- A two-column **body grid**: the left column is Markdown; the right column is
  an image or a URL rendered as a QR code (e.g. a how-to video)
- Two footer QR codes: **Log use** and **Edit**

Lantern enforces the single page: if an edit makes a sheet too long, it's
flagged and held out of the print queue until it fits — your text is always
saved.

## Quick start

You need [Docker](https://docs.docker.com/get-docker/). From the project folder:

```bash
docker compose up --build
```

Open **http://localhost:8080** and create your first sheet.

For phones on your network to scan the QR codes, set `BASE_URL` to the address
of the machine running Lantern (not `localhost`):

```bash
BASE_URL=http://192.168.1.50:8080 EDIT_PIN=your-wall-pin docker compose up --build
```

> Find the host's address with `ip addr` (the `192.168.x.x` or `10.x.x.x` one).

## Configuration

All settings are environment variables (see `.env.example`):

| Variable | Default | What it does |
|---|---|---|
| `BASE_URL` | `http://localhost:8080` | The address baked into every QR code. **Set this to a LAN IP/hostname** so phones can reach it. |
| `EDIT_PIN` | `changeme` | The shared PIN required to edit or create sheets. **Change this.** |
| `PIN_ENABLED` | `1` | Set to `0` to drop the PIN gate entirely (fully open). |
| `PAGE_SIZE` | `letter` | Page size: `letter` (US) or `a4`. Also switchable in Settings. |
| `DATA_DIR` | `/data` | Where sheets, history, the database, images, and the logo live. |
| `REPO_URL` | this repo | Link shown in the printed sheet footer. |
| `SEED_SAMPLES` | `1` | Seed two example sheets on first run. `0` for an empty start. |

Your data — sheet content (with full git history), the usage log, uploaded
images, custom templates, and your logo — all lives under `DATA_DIR`. Back that
up and you've backed up everything.

## Self-hosting

Lantern is a single container. Map a host directory to the container's `/data`
to persist everything, set `BASE_URL` and `EDIT_PIN`, and publish port `8080`.
A ready-made compose file and a step-by-step guide for **TrueNAS SCALE** (using
a dataset bind-mount so snapshots back it up) are in
[`deploy/truenas/`](deploy/truenas/) and [`docs/truenas.md`](docs/truenas.md);
the same pattern works on any Docker host.

## For developers

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
PIN_ENABLED=0 DATA_DIR=./data uvicorn app.main:app --reload --port 8080
pytest                      # run the test suite
```

PDF rendering needs headless Chromium (bundled in the Docker image); the local
dev server runs without it and simply skips PDF generation.

See [`DESIGN.md`](DESIGN.md) for the architecture, data model, and routes, and
[`UBIQUITOUS_LANGUAGE.md`](UBIQUITOUS_LANGUAGE.md) for the project glossary (the
terms used in the code and UI).
