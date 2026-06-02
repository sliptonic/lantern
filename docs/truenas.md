# Deploying Lantern on TrueNAS SCALE

Lantern is a single container. The only thing that needs to persist is its
`/data` directory — sheets (with full git history), the usage-log database,
custom templates, and the uploaded logo. Bind-mount that to a **TrueNAS
dataset** and your normal snapshot/replication schedule backs up everything.

## 1. Create a dataset

In the TrueNAS UI: **Datasets → Add dataset**, e.g. `tank/apps/lantern`. Its
host path will be something like `/mnt/tank/apps/lantern`.

## 2. Configure

From this repo, on the TrueNAS box:

```bash
cd deploy/truenas
cp .env.example .env
# edit .env:
#   LANTERN_DATA=/mnt/tank/apps/lantern   (the dataset path from step 1)
#   BASE_URL=http://<server-LAN-IP>:8080  (what phones will scan)
#   EDIT_PIN=<a real PIN you post on the wall>
#   PAGE_SIZE=letter | a4
```

> **`BASE_URL` must be reachable from phones.** Give the TrueNAS box a
> reserved/static IP on your LAN and use that. `localhost` will not work from a
> phone.

## 3. Run

```bash
docker compose up -d --build
```

Then open `http://<server-LAN-IP>:8080`. The compose file refuses to start
unless `BASE_URL`, `EDIT_PIN`, and `LANTERN_DATA` are set, so you can't
accidentally ship with the placeholder PIN.

On newer SCALE releases you can instead paste `deploy/truenas/docker-compose.yml`
into **Apps → Discover → Custom App → Install via YAML**, supplying the same
environment variables and the dataset host-path mount (`/data`).

## 4. Backups

Everything lives under the dataset you mounted at `/data`:

```
/mnt/tank/apps/lantern/
├── content/      # sheets as markdown — a full git repo (history + revert)
├── templates/    # your custom sheet templates
├── lantern.db    # usage log + print-queue state
└── logo.png      # uploaded logo
```

Add a **Periodic Snapshot Task** (and optionally **Replication**) on the
dataset. To restore, roll the dataset back to a snapshot — no app-specific
steps needed. Because sheet content is a git repo, you also have per-edit
history inside the app independent of snapshots.

## Updating

```bash
cd deploy/truenas
git pull
docker compose up -d --build
```

Your data is untouched — it lives in the dataset, not the container.
