"""Domain models. Names follow UBIQUITOUS_LANGUAGE.md."""
from __future__ import annotations

from dataclasses import dataclass, field

# Right-hand content kinds for a body Row.
ROW_NONE = "none"
ROW_IMAGE = "image"
ROW_QR = "qr"


@dataclass
class Link:
    """A labelled URL — used for Software Links and Manual Links."""
    label: str
    url: str


@dataclass
class Contact:
    """The Contact Person for a Machine."""
    name: str = ""
    info: str = ""  # free text: email, phone, shop hours


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
    """An Info-Sheet: the single-page document for one Machine.

    Structured Fields live as frontmatter; the Procedure is a grid of body
    `rows` (left Markdown + an optional image or QR on the right). Persisted as
    `content/sheets/<slug>.md` and versioned in git.
    """
    slug: str
    machine: str
    contact: Contact = field(default_factory=Contact)
    software_links: list[Link] = field(default_factory=list)
    manual_links: list[Link] = field(default_factory=list)
    training_required: str = ""
    rows: list[BodyRow] = field(default_factory=list)

    # --- serialization to/from frontmatter dict ---
    def frontmatter(self) -> dict:
        return {
            "slug": self.slug,
            "machine": self.machine,
            "contact": {"name": self.contact.name, "info": self.contact.info},
            "software_links": [{"label": lk.label, "url": lk.url} for lk in self.software_links],
            "manual_links": [{"label": lk.label, "url": lk.url} for lk in self.manual_links],
            "training_required": self.training_required,
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
            machine=meta.get("machine", meta["slug"]),
            contact=Contact(name=contact.get("name", ""), info=contact.get("info", "")),
            software_links=[Link(**lk) for lk in (meta.get("software_links") or [])],
            manual_links=[Link(**lk) for lk in (meta.get("manual_links") or [])],
            training_required=meta.get("training_required", ""),
            rows=rows,
        )
