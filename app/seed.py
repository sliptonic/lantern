"""First-run sample content.

When the content store has no sheets yet, seed a couple of example Info-Sheets
so a new operator can immediately see what Lantern produces and how editing,
logging, and printing work. Seeding is skipped once any sheet exists.
"""
from __future__ import annotations

from . import content, state
from .models import Contact, Link, Sheet

_SAMPLES = [
    Sheet(
        slug="prusa-mk4-3d-printer",
        machine="Prusa MK4 3D Printer",
        contact=Contact(name="Sam Rivera", info="sam@makerspace.org · Tue/Thu evenings"),
        training_required="Intro to FDM printing (30 min) + badge sign-off",
        software_links=[Link(label="PrusaSlicer", url="https://www.prusa3d.com/prusaslicer/")],
        manual_links=[Link(label="MK4 Handbook (PDF)", url="https://help.prusa3d.com/")],
        body="""## Before you start
- Check the **build plate is clean** — wipe with IPA if greasy.
- Confirm the spool has enough filament for your print.

## Printing
1. Slice your model in **PrusaSlicer** using the *MK4 — 0.2mm SPEED* profile.
2. Export G-code to the USB stick (or send over the network).
3. On the printer: **Print → select file → confirm filament type**.
4. Stay for the **first layer** — make sure it sticks before walking away.

## When you're done
- Remove your print and **pop off any skirt/brim** from the plate.
- Leave the plate clean and the area tidy.
- **Scan the LOG QR** to record your session.

> ⚠️ Never leave a print running overnight unattended.
""",
    ),
    Sheet(
        slug="epilog-laser-cutter",
        machine="Epilog Laser Cutter",
        contact=Contact(name="Dana Kim", info="dana@makerspace.org · weekends"),
        training_required="Laser safety course + supervised first cut. NO untrained use.",
        software_links=[Link(label="Inkscape", url="https://inkscape.org/")],
        manual_links=[Link(label="Epilog Manual", url="https://www.epiloglaser.com/")],
        body="""## Safety first
- **Know your material.** Only cut approved materials (see the posted list).
  **Never** cut PVC/vinyl — it releases chlorine gas.
- Confirm the **exhaust fan is ON** before lasing.
- **Never leave the laser unattended** while it is running. Keep a view of the bed.

## Cutting
1. Set up artwork in **Inkscape**: hairline (0.01mm) red strokes = cut, black fill = engrave.
2. Place material, **set focus**, and run **Air Assist**.
3. Send the job and **close the lid** — the laser won't fire while open.
4. Watch for **flare-ups**. If flames persist, hit the **E-stop**.

## After
- Let the exhaust run ~30s, then remove your parts.
- Empty small offcuts; wipe the bed.
- **Scan the LOG QR** to record your session.
""",
    ),
]


def seed_if_empty() -> int:
    """Create sample sheets if none exist. Returns the number created."""
    if content.list_slugs():
        return 0
    for sheet in _SAMPLES:
        content.save(sheet, author="Lantern", message=f"Seed sample: {sheet.slug}")
        state.mark_saved(sheet.slug, overflowing=False)
    return len(_SAMPLES)
