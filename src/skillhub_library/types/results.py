"""What ``search``, ``install`` and ``uninstall`` answer with."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Self

from .aliases import TargetAction
from .skill import Skill
from .targets import Target

__all__ = ["SearchResult", "InstallResult", "UninstallResult"]


@dataclass(frozen=True)
class SearchResult:
    """Iterates and ``len()``s like a list of :class:`Skill`, but keeps ``total``."""

    items: tuple[Skill, ...] = ()
    total: int = 0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``search`` answer from the CLI's decoded JSON."""
        hits = payload.get("items")
        items = tuple(Skill.from_payload(h) for h in hits) if isinstance(hits, list) else ()
        total = payload.get("total")
        return cls(items=items, total=total if isinstance(total, int) else len(items))

    def __iter__(self) -> Iterator[Skill]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Skill:
        return self.items[index]


@dataclass(frozen=True)
class InstallResult:
    """Where an install put the skill."""

    namespace: str = ""
    slug: str = ""
    installed_targets: tuple[Target, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``install`` answer from the CLI's decoded JSON."""
        return cls(
            namespace=payload.get("namespace", ""),
            slug=payload.get("slug", ""),
            installed_targets=_parse_targets(payload, "installed"),
        )


@dataclass(frozen=True)
class UninstallResult:
    """``scope`` is the CLI's ``local``/``remote``."""

    scope: str = ""
    removed_targets: tuple[Target, ...] = ()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``remove`` answer from the CLI's decoded JSON."""
        return cls(
            scope=payload.get("scope", ""),
            removed_targets=_parse_targets(payload, "removed"),
        )


def _parse_targets(payload: dict[str, Any], action: TargetAction) -> tuple[Target, ...]:
    """Read the payload's ``installed`` or ``removed`` list into targets."""
    entries = payload.get(action)
    return tuple(Target.from_payload(e) for e in entries) if isinstance(entries, list) else ()
