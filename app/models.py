# SPDX-License-Identifier: AGPL-3.0-or-later
"""Domain models for Info-Sheets. Terms follow UBIQUITOUS_LANGUAGE.md."""
from __future__ import annotations

from dataclasses import dataclass, field

# Right-hand content kinds for a body Row.
ROW_NONE = "none"
ROW_IMAGE = "image"
ROW_QR = "qr"


@dataclass
class Contact:
    """The person responsible for the subject of a sheet."""
    name: str = ""
    info: str = ""  # free text: email, phone, hours


@dataclass
class BodyRow:
    """One row of the two-column body grid.

    `left` is Markdown. `right` is one of: nothing, an uploaded image, or a URL
    rendered as a QR code (e.g. a video link). For an image, `value` is the
    image token (filename in the image pool); for a qr, `value` is the URL.
    """
    left: str = ""
    kind: str = ROW_NONE  # none | image | qr
    value: str = ""

    def as_dict(self) -> dict:
        return {"left": self.left, "kind": self.kind, "value": self.value}

    @classmethod
    def from_dict(cls, d: dict) -> "BodyRow":
        kind = d.get("kind", ROW_NONE)
        if kind not in (ROW_NONE, ROW_IMAGE, ROW_QR):
            kind = ROW_NONE
        return cls(left=d.get("left", ""), kind=kind, value=d.get("value", ""))


@dataclass
class Sheet:
    """An Info-Sheet: the single-page document for one posted procedure.

    Structured fields live as frontmatter; the body is a grid of `rows`
    (left Markdown + an optional image or QR on the right). Persisted as
    `content/sheets/<slug>.md` and versioned in git.
    """
    slug: str
    title: str
    contact: Contact = field(default_factory=Contact)
    requirements: str = ""
    rows: list[BodyRow] = field(default_factory=list)

    # --- serialization to/from frontmatter dict ---
    def frontmatter(self) -> dict:
        return {
            "slug": self.slug,
            "title": self.title,
            "contact": {"name": self.contact.name, "info": self.contact.info},
            "requirements": self.requirements,
            "rows": [r.as_dict() for r in self.rows],
        }

    @classmethod
    def from_frontmatter(cls, meta: dict, body: str) -> "Sheet":
        contact = meta.get("contact") or {}
        if meta.get("rows") is not None:
            rows = [BodyRow.from_dict(r) for r in meta["rows"]]
        elif (body or "").strip():
            # Legacy sheets stored a single markdown body — migrate to one row.
            rows = [BodyRow(left=body)]
        else:
            rows = []
        return cls(
            slug=meta["slug"],
            # `machine` and `training_required` are the legacy field names.
            title=meta.get("title") or meta.get("machine") or meta["slug"],
            contact=Contact(name=contact.get("name", ""), info=contact.get("info", "")),
            requirements=meta.get("requirements") or meta.get("training_required", ""),
            rows=rows,
        )
