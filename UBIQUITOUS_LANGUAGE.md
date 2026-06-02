# Lantern — Ubiquitous Language

A shared glossary for the project. Every term here means **exactly one thing**
in conversation, code, UI text, and docs. Code identifiers (classes, routes,
columns, template vars) use these words verbatim. If a concept needs a new name,
add it here first.

---

## Core domain

**Info-Sheet** *(short: **Sheet**)*
The single-page document for one posted procedure. Stored as one Markdown file
with frontmatter, versioned in git. Rendered to a branded PDF for posting. The
central entity of the system.

**Title**
The name of a Sheet's subject — a machine, station, room, process, anything. A
Structured Field; shown as the Sheet's heading.

**Slug**
The stable, URL-safe identifier for a Sheet (e.g. `laser-cutter`). Derived from
the Title on creation and never changed — it is baked into printed QR codes.
Drives the filename (`<slug>.md`), all routes, and both QR targets.

**Structured Fields**
The known, typed fields in a Sheet's frontmatter, rendered into fixed zones of
the Template: Title, Contact, Software Links, Manual Links, Requirements.

**Body**
The main content of a Sheet — a two-column grid of **Body Rows**.

**Body Row**
One row of the Body grid: a **left** side of freeform Markdown and a **right**
side that is one of nothing, an **Image**, or a **QR Row** (a URL rendered as a
QR code). Authors add/remove rows in the Editor.

**Image**
A picture embedded in a Body Row's right side. Uploaded by the author and kept
in a flat pool in the data volume (referenced by a token); inlined into the
rendered PDF. Not git-versioned (unlike the Markdown).

**QR Row**
A Body Row whose right side is a URL rendered as a QR code on the Sheet — used
to link out to videos or other resources by phone scan.

**Contact** *(the **Contact Person**)*
The person responsible for / knowledgeable about a Sheet's subject. A Structured
Field: a name plus free text info (email, phone, hours).

**Requirements**
A Structured Field stating what training, sign-off, or prerequisites apply
before using the subject. Informational text.

**Software Link / Manual Link**
Structured Fields: labelled URLs for downloadable software and for manuals.
Rendered as a list on the Sheet.

---

## QR codes & walk-up flows

**Log QR**
The QR code on a printed Sheet that opens the Usage Log form. Encodes
`${BASE_URL}/sheet/<slug>/log`.

**Edit QR**
The QR code on a printed Sheet that opens the Editor. Encodes
`${BASE_URL}/sheet/<slug>/edit`.

**Walk-up User**
Anyone at a posted Sheet using only their phone and a QR code — no app, no
account. The primary actor for logging and edit-triggering.

**Base URL**
The configurable root address (`BASE_URL`) that all QR codes and absolute links
are built from. Lets the same build work behind a static LAN IP, an mDNS
hostname, or a real domain.

---

## Usage logging

**Usage Log**
The append-only record of who used a Sheet's subject and what they did. Stored
in SQLite (never in git — it is event data, not document content).

**Log Entry**
One row in the Usage Log: slug, name (typed, unverified), activity, notes,
timestamp.

---

## Editing & versioning

**Editor**
The editing UI for a Sheet (Structured Fields form + the Body row grid + live
preview). Also the noun for the act of editing.

**Contributor**
Anyone who edits a Sheet. Identified only by a typed name (unverified); gated by
the PIN.

**PIN**
The shared secret posted on the wall, required to edit or create Sheets. A soft
gate, not authentication. Enforcement is toggleable (`PIN_ENABLED`).

**Revision** *(a.k.a. **Version**, backed by a **Commit**)*
One saved state of a Sheet. Each save creates a git Commit. The full history of
a Sheet is its sequence of Revisions.

**Revert**
Restoring a Sheet to an earlier Revision by committing that prior content as a
new Revision (history is preserved, never rewritten).

**Archive**
Retiring a Sheet: hidden from the Dashboard and Print Queue, but content and
history are preserved and the action is reversible (Unarchive).

---

## Rendering & the page

**Template**
A standalone Jinja layout a Sheet is rendered through. Built-in Templates ship
with the app; custom Templates are authored in Settings and persist in the data
volume. The active Template is a setting.

**Branding / Logo**
The identity applied by the Template — primarily the uploaded Logo, shown in the
Sheet header. Distinct from the Lantern brand mark in the footer.

**Render**
Producing the final PDF: Sheet → Template HTML → headless Chromium → PDF.

**Page Size**
US Letter or A4. Configurable (`PAGE_SIZE`, default Letter) and switchable in
Settings. A Sheet must fit exactly one page of the active size.

**Overflow / Overflowing**
The state of a Sheet whose Render exceeds one page. An Overflowing Sheet can
still be saved, but is flagged and **blocked from the Print Queue** until it
fits.

---

## Printing

**Print Queue** *(short: **Queue**)*
The list of Sheets that have changed since they were last printed and need a
fresh physical copy. Backed by SQLite state, not a real printer spool.

**Dirty / Needs-Printing**
The state of a Sheet that has changed since it was last printed — set when a
fitting Sheet is saved, cleared on Mark Printed. A Dirty Sheet appears in the
Print Queue unless it is Overflowing or Archived.

**Last-Printed Version**
The Commit of the Revision most recently marked as printed. Comparing it to the
current Revision determines whether a Sheet is Dirty.

**Mark Printed**
The Print Operator's action that removes a Sheet from the Queue and records the
current Revision as the Last-Printed Version. Can be done per-sheet or for the
whole Queue at once.

**Print Operator**
The person at the computer with the attached printer who works the Queue. Uses
the browser's print dialog on the rendered PDF — no direct printer integration.

---

## Navigation & roles

**Dashboard** *(a.k.a. **Index**)*
The central organizer view: lists every active Sheet with status (Dirty,
Overflowing, last-logged), plus the Print Queue, Recent Activity, and Archived
Sheets. Home of admin actions.

**Recent Activity**
A feed of recent Log Entries surfaced on the Dashboard.

**Settings**
Admin configuration: Logo, active Template (and custom Template editing), and
Page Size. Saving changes is PIN-gated.
