"""Typed views over the CLI's JSON payloads.

``from_payload`` never raises: unknown keys are ignored, missing keys fall back
to a default, and ``raw`` keeps the original payload so nothing is lost. The
CLI owns the shape -- adding a field to it must not break the wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Skill", "SearchResult", "Target", "InstallResult", "RemoveResult"]


@dataclass(frozen=True)
class Skill:
    """One search hit."""

    namespace: str = ""
    slug: str = ""
    latest_version: str = ""
    summary: str = ""
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload):
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            namespace=payload.get("namespace", ""),
            slug=payload.get("slug", ""),
            latest_version=payload.get("latestVersion", ""),
            summary=payload.get("summary", ""),
            raw=payload,
        )


@dataclass(frozen=True)
class SearchResult:
    """Iterates and ``len()``s like a list of :class:`Skill`, but keeps ``total``."""

    items: tuple[Skill, ...] = ()
    total: int = 0

    @classmethod
    def from_payload(cls, payload):
        payload = payload if isinstance(payload, dict) else {}
        hits = payload.get("items")
        items = tuple(Skill.from_payload(h) for h in hits) if isinstance(hits, list) else ()
        total = payload.get("total")
        return cls(items=items, total=total if isinstance(total, int) else len(items))

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


@dataclass(frozen=True)
class Target:
    """One place a skill was installed to or removed from.

    ``install`` reports only ``agent``/``directory``; ``remove`` adds
    ``namespace`` and ``existed``, which stay at their defaults otherwise.
    """

    agent: str = ""
    directory: str = ""  # the CLI's "dir"
    namespace: str = ""
    existed: bool | None = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload):
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            agent=payload.get("agent", ""),
            directory=payload.get("dir", ""),
            namespace=payload.get("namespace", ""),
            existed=payload.get("existed"),
            raw=payload,
        )


@dataclass(frozen=True)
class InstallResult:
    """Where an install put the skill."""

    namespace: str = ""
    slug: str = ""
    installed: tuple[Target, ...] = ()
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload):
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            namespace=payload.get("namespace", ""),
            slug=payload.get("slug", ""),
            installed=_targets(payload, "installed"),
            raw=payload,
        )


@dataclass(frozen=True)
class RemoveResult:
    """What a removal took away. ``scope`` is the CLI's ``local``/``remote``."""

    scope: str = ""
    removed: tuple[Target, ...] = ()
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload):
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            scope=payload.get("scope", ""),
            removed=_targets(payload, "removed"),
            raw=payload,
        )


def _targets(payload, key):
    entries = payload.get(key)
    return tuple(Target.from_payload(e) for e in entries) if isinstance(entries, list) else ()
