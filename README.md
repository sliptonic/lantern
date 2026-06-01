<h1 align="center">🏮 Lantern</h1>

<p align="center"><em>Printable, always-current info sheets for every machine in your makerspace.</em></p>

---

Lantern makes the one-page sheets you hang on the wall next to equipment — the
ones with the contact person, the startup checklist, the manual link, and the
training requirements. It keeps them **easy to fix**, **always versioned**, and
**ready to reprint**, and it lets anyone **log that they used a machine** with a
single phone scan.

No app to install. No account to create. Walk up, scan a QR code, done.

## Why it exists

Wall sheets rot. The contact person leaves, a step changes, the manual moves —
and the paper by the machine is now wrong, with no obvious way to fix it. Lantern
turns each sheet into a living document:

- **See it** — a clean, branded, single-page sheet posted by the machine.
- **Fix it** — spot an error, scan the *edit* QR, correct it in your browser. The
  old version is never lost.
- **Log it** — scan the *log* QR, type your name and what you did. That's the
  whole usage log.
- **Reprint it** — corrected sheets land in a print queue for whoever's near the
  printer.

## How people use it

**🧑‍🔧 Someone using a machine**
Reads the posted sheet. To record their session, scans the **Log** QR code and
fills in a short form (name · what they did · optional notes). No login.

**✏️ Someone fixing a sheet**
Scans the **Edit** QR code, edits in Markdown in their browser, enters the shared
**Space PIN** (posted on the wall), and saves. Every save is a new version —
mistakes are one click to revert.

**🖨️ Whoever prints**
Opens the **Print Queue** on the computer with the printer, sees every sheet
that changed since it was last printed, opens the PDF, and prints it on plain
US Letter paper. Marks it printed and it leaves the queue.

**🗂️ Whoever organizes**
Uses the **Dashboard** to see all machines at a glance — which sheets need
printing, which are too long to fit one page, and recent activity — and to
create new sheets.

## What's on a sheet

Each sheet is one US Letter page with a uniform, logo-branded layout:

- Machine name + your makerspace logo
- Contact person and how to reach them
- Training required before use
- Links to software downloads and manuals
- A free-form **procedure / checklist** (written in Markdown)
- Two QR codes in the footer: **Log use** and **Edit**

Lantern enforces the single page: if an edit makes a sheet too long, it's flagged
and held out of the print queue until it fits — but your text is always saved.

## Quick start

You need [Docker](https://docs.docker.com/get-docker/). From the project folder:

```bash
docker compose up --build
```

Open **http://localhost:8080** and create your first sheet.

To let phones on your network actually scan the QR codes, set `BASE_URL` to the
address of the machine running Lantern (not `localhost`):

```bash
BASE_URL=http://192.168.1.50:8080 EDIT_PIN=your-wall-pin docker compose up --build
```

> Find your machine's address with `ip addr` (the `192.168.x.x` or `10.x.x.x` one).

## Configuration

All settings are environment variables (see `.env.example`):

| Variable | Default | What it does |
|---|---|---|
| `BASE_URL` | `http://localhost:8080` | The address baked into every QR code. **Set this to a LAN IP/hostname** so phones can reach it. |
| `EDIT_PIN` | `changeme` | The shared Space PIN required to edit or create sheets. **Change this.** |
| `PIN_ENABLED` | `1` | Set to `0` to drop the PIN gate entirely (fully open). |
| `DATA_DIR` | `/data` | Where sheets, history, the database, and the logo live. |

Your data — sheet content (with full git history), the usage log, and your logo —
lives in one place (`DATA_DIR`). Back that up and you've backed up everything.

## Running on TrueNAS SCALE

Lantern is a single container designed to run on a locally hosted TrueNAS SCALE
server. There's a ready-made bind-mount compose file and a step-by-step guide:

- **Guide:** [`docs/truenas.md`](docs/truenas.md)
- **Compose + env template:** [`deploy/truenas/`](deploy/truenas/)

In short: create a dataset, bind-mount it to the container's `/data` (so TrueNAS
snapshots cover all your sheets, history, logs, templates, and logo), set
`BASE_URL` to the server's LAN address and `EDIT_PIN` to your wall PIN, and
publish port `8080`.

## For developers

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
PIN_ENABLED=0 DATA_DIR=./data uvicorn app.main:app --reload --port 8080
pytest                      # run the test suite
```

PDF rendering needs headless Chromium (bundled in the Docker image); the local
dev server runs without it and simply skips PDF generation.

- **`DESIGN.md`** — architecture and the decisions behind it.
- **`UBIQUITOUS_LANGUAGE.md`** — the project glossary; the words here are the
  words used in the code.

## Status

Early, working scaffold: create/edit sheets with versioned history, usage
logging, single-page PDF rendering with overflow detection, and the print queue
are all in place. See `DESIGN.md` for the roadmap.
