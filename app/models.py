"""Domain models. Names follow UBIQUITOUS_LANGUAGE.md."""
from __future__ import annotations

from dataclasses import dataclass, field


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
class Sheet:
    """An Info-Sheet: the single-page document for one Machine.

    Structured Fields live as frontmatter; `body` is the freeform markdown
    Procedure. Persisted as `content/sheets/<slug>.md` and versioned in git.
    """
    slug: str
    machine: str
    contact: Contact = field(default_factory=Contact)
    software_links: list[Link] = field(default_factory=list)
    manual_links: list[Link] = field(default_factory=list)
    training_required: str = ""
    body: str = ""  # the Procedure (markdown)

    # --- serialization to/from frontmatter dict ---
    def frontmatter(self) -> dict:
        return {
            "slug": self.slug,
            "machine": self.machine,
            "contact": {"name": self.contact.name, "info": self.contact.info},
            "software_links": [{"label": lk.label, "url": lk.url} for lk in self.software_links],
            "manual_links": [{"label": lk.label, "url": lk.url} for lk in self.manual_links],
            "training_required": self.training_required,
        }

    @classmethod
    def from_frontmatter(cls, meta: dict, body: str) -> "Sheet":
        contact = meta.get("contact") or {}
        return cls(
            slug=meta["slug"],
            machine=meta.get("machine", meta["slug"]),
            contact=Contact(name=contact.get("name", ""), info=contact.get("info", "")),
            software_links=[Link(**lk) for lk in (meta.get("software_links") or [])],
            manual_links=[Link(**lk) for lk in (meta.get("manual_links") or [])],
            training_required=meta.get("training_required", ""),
            body=body,
        )
