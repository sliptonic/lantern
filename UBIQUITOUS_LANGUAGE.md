# Lantern — Ubiquitous Language

A shared glossary for the project. Every term here should mean **exactly one
thing** in conversation, code, UI text, and docs. If a concept needs a new
name, add it here first. Code identifiers (classes, routes, columns, template
vars) should use these words verbatim.

Status: living document. Add/refine terms as the model sharpens.

---

## Core domain

**Info-Sheet** *(short: **Sheet**)*
The single-page document for one piece of equipment. Stored as one markdown
file with frontmatter, versioned in git. Rendered to a branded PDF for wall
posting. The central entity of the system.

**Machine** *(a.k.a. **Equipment**)*
The physical thing in the makerspace a Sheet describes (laser cutter, lathe,
3D printer…). One Machine ↔ one Sheet.

**Slug**
The stable, URL-safe identifier for a Sheet (e.g. `laser-cutter`). Never
changes once created — it is baked into printed QR codes. Drives the filename
(`<slug>.md`), all routes, and both QR targets.

**Frontmatter Fields** *(the **Structured Fields**)*
The known, typed fields stored in a Sheet's YAML frontmatter and rendered into
fixed zones of the Template: Machine name, Contact, Software Links, Manual
Links, Training Requirement. Guarantees uniform layout.

**Body** *(a.k.a. **Procedure**)*
The main content of a Sheet — a two-column grid of **Body Rows**. Not a
Structured Field.

**Body Row**
One row of the Body grid: a **left** side of freeform Markdown and a **right**
side that is one of nothing, an **Image**, or a **QR Row** (a URL rendered as a
QR code, e.g. a how-to video). Authors add/remove rows in the Editor.

**Image**
A picture embedded in a Body Row's right side. Uploaded by the author and kept
in a flat pool in the data volume (referenced by a token); inlined into the
rendered PDF. Not git-versioned (unlike the Markdown).

**QR Row**
A Body Row whose right side is a URL rendered as a QR code on the Sheet — used
to link out to videos or other resources by phone scan.

**Contact** *(the **Contact Person**)*
The person responsible for / knowledgeable about a Machine. A Structured Field:
a name plus free text info (email, phone, shop hours).

**Training Requirement**
A Structured Field stating what training/sign-off is required before using the
Machine. Informational text in v1 (not linked to training records).

**Software Link / Manual Link**
Structured Fields: labelled URLs for downloadable software and for the Machine's
manual(s). Rendered as a list in the Template.

---

## QR codes & walk-up flows

**Log QR**
The QR code on a printed Sheet that opens the Usage Log form for that Machine.
Encodes `${BASE_URL}/sheet/<slug>/log`.

**Edit QR**
The QR code on a printed Sheet that opens the Editor for that Sheet. Encodes
`${BASE_URL}/sheet/<slug>/edit`.

**Walk-up User**
Anyone at a Machine using only their phone and a QR code — no app, no account.
The primary actor for logging and edit-triggering.

**Base URL**
The configurable root address (`BASE_URL`, env/config) that all QR codes and
absolute links are built from. Lets the same build work behind a static LAN IP,
an mDNS hostname, or a real domain.

---

## Usage logging

**Usage Log**
The append-only record of who used a Machine and what they did. Stored in
SQLite (never in git — it is event data, not document content).

**Log Entry**
One row in the Usage Log: Machine (slug), name (typed, unverified), activity,
notes, timestamp.

---

## Editing & versioning

**Editor**
The markdown editing UI for a Sheet (Structured Fields form + Body markdown box
+ live preview). Also the noun for the act of editing.

**Contributor**
Anyone who edits a Sheet. Identified only by a typed name (unverified); gated by
the Space PIN.

**Space PIN** *(short: **PIN**)*
The shared secret posted on the wall, required to edit or create Sheets. Soft
gate, not authentication. Enforcement is toggleable (`PIN_ENABLED`).

**Revision** *(a.k.a. **Version**, backed by a **Commit**)*
One saved state of a Sheet. Each save creates a git Commit. The full history of
a Sheet is its sequence of Revisions.

**Revert**
Restoring a Sheet to an earlier Revision by committing that prior content as a
new Revision (history is preserved, never rewritten).

---

## Rendering & the page

**Template**
The single uniform HTML/CSS layout every Sheet is rendered through. Defines the
zones for Structured Fields, Body, QR codes, and Branding.

**Branding**
The makerspace identity applied by the Template — primarily the uploaded Logo.

**Logo**
The makerspace image, uploaded once via admin Settings, shown on every Sheet.

**Render**
Producing the final PDF: Markdown + Frontmatter → Template HTML → headless
Chromium → PDF (US **Letter**, 8.5×11 in).

**Letter Page**
The output size: US Letter, 8.5×11 inches. (The brief said "legal"; 8.5×11 is
Letter — Legal is 8.5×14.) A Sheet must fit exactly one Letter Page.

**Overflow / Overflowing**
The state of a Sheet whose Render exceeds one Letter Page. An Overflowing Sheet
can still be saved, but is flagged and **blocked from the Print Queue** until it
fits.

---

## Printing

**Print Queue** *(short: **Queue**)*
The list of Sheets that have changed since they were last printed and need a
fresh physical copy. Backed by SQLite state, not a real printer spool.

**Dirty / Needs-Printing**
The state of a Sheet whose current Revision is newer than its Last-Printed
Version (and which is not Overflowing). Dirty Sheets appear in the Queue.

**Last-Printed Version**
The Commit of the Revision most recently marked as printed. Comparing it to the
current Revision determines whether a Sheet is Dirty.

**Mark Printed**
The Print Operator's action that removes a Sheet from the Queue and records the
current Revision as the Last-Printed Version.

**Print Operator**
The person at the machine with the attached printer who works the Queue. Uses
the browser's print dialog on the rendered PDF — no direct printer integration.

---

## Navigation & roles

**Dashboard** *(a.k.a. **Index**)*
The central organizer view: lists every Sheet with status (Dirty, Overflowing,
last-logged), plus the Print Queue and Recent Activity. Home of admin actions.

**Recent Activity**
A feed of recent Log Entries and Revisions surfaced on the Dashboard.

**Settings**
Admin configuration: Logo upload, PIN, Base URL, PIN toggle. PIN-gated.
