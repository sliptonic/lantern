"""Git-backed content store for Info-Sheets.

Each Sheet is one markdown file with YAML frontmatter at
`content/sheets/<slug>.md`. Every save is a git Commit, so history, diff, and
Revert come for free. This module owns all git interaction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import frontmatter
from git import Repo

from .config import get_settings
from .models import Sheet

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Derive a stable, URL-safe Slug from a machine name."""
    slug = _SLUG_RE.sub("-", text.strip().lower()).strip("-")
    return slug or "sheet"


@dataclass
class Revision:
    """One saved Version of a Sheet, backed by a git Commit."""
    commit: str
    author: str
    message: str
    when: str


def _repo() -> Repo:
    """Open (initializing on first use) the content git repository."""
    settings = get_settings()
    settings.sheets_dir.mkdir(parents=True, exist_ok=True)
    git_dir = settings.content_dir / ".git"
    if git_dir.exists():
        return Repo(settings.content_dir)
    repo = Repo.init(settings.content_dir)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Lantern")
        cw.set_value("user", "email", "lantern@localhost")
    return repo


def _path_for(slug: str):
    return get_settings().sheets_dir / f"{slug}.md"


def _relpath(slug: str) -> str:
    return f"sheets/{slug}.md"


# --- reads -----------------------------------------------------------------

def list_slugs() -> list[str]:
    sheets_dir = get_settings().sheets_dir
    if not sheets_dir.exists():
        return []
    return sorted(p.stem for p in sheets_dir.glob("*.md"))


def exists(slug: str) -> bool:
    return _path_for(slug).exists()


def load(slug: str) -> Sheet | None:
    path = _path_for(slug)
    if not path.exists():
        return None
    post = frontmatter.load(path)
    meta = dict(post.metadata)
    meta.setdefault("slug", slug)
    return Sheet.from_frontmatter(meta, post.content)


def history(slug: str) -> list[Revision]:
    """All Revisions of a Sheet, newest first."""
    repo = _repo()
    rel = _relpath(slug)
    revs: list[Revision] = []
    for c in repo.iter_commits(paths=rel):
        revs.append(
            Revision(
                commit=c.hexsha,
                author=str(c.author.name),
                message=str(c.message).strip(),
                when=c.committed_datetime.isoformat(),
            )
        )
    return revs


def current_commit(slug: str) -> str | None:
    revs = history(slug)
    return revs[0].commit if revs else None


# --- writes ----------------------------------------------------------------

def save(sheet: Sheet, author: str, message: str | None = None) -> str:
    """Persist a Sheet and commit it. Returns the new commit sha (Revision)."""
    repo = _repo()
    path = _path_for(sheet.slug)
    post = frontmatter.Post(sheet.body, **sheet.frontmatter())
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    rel = _relpath(sheet.slug)
    repo.index.add([rel])
    author_name = author.strip() or "anonymous"
    commit = repo.index.commit(
        message or f"Edit {sheet.slug}",
        author=_actor(author_name),
        committer=_actor(author_name),
    )
    return commit.hexsha


def revert(slug: str, commit: str, author: str) -> str:
    """Restore a Sheet's content from an earlier Revision as a new Revision."""
    repo = _repo()
    rel = _relpath(slug)
    blob = repo.commit(commit).tree / rel
    _path_for(slug).write_bytes(blob.data_stream.read())
    repo.index.add([rel])
    author_name = author.strip() or "anonymous"
    new = repo.index.commit(
        f"Revert {slug} to {commit[:8]}",
        author=_actor(author_name),
        committer=_actor(author_name),
    )
    return new.hexsha


def _actor(name: str):
    from git import Actor
    return Actor(name, "lantern@localhost")
