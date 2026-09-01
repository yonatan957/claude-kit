"""What ``search``, ``install`` and ``uninstall`` answer with."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Self

from skillhub_library.errors import MalformedAnswerError
from skillhub_library.types.aliases import TargetAction
from skillhub_library.types.skill import Skill
from skillhub_library.types.targets import Target

__all__ = ["SearchResult", "InstallResult", "UninstallResult"]


@dataclass(frozen=True)
class SearchResult:
    """Iterates and ``len()``s like a list of :class:`Skill`, but keeps ``total``."""

    skills: tuple[Skill, ...]
    total: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``search`` answer from the CLI's decoded JSON."""
        try:
            return cls(
                skills=tuple(Skill.from_payload(h) for h in payload["items"]),
                total=payload["total"],
            )
        except (KeyError, TypeError) as unusable:
            raise MalformedAnswerError(f"unusable search answer: {unusable}") from unusable

    def __iter__(self) -> Iterator[Skill]:
        return iter(self.skills)

    def __len__(self) -> int:
        return len(self.skills)

    def __getitem__(self, index: int) -> Skill:
        return self.skills[index]


@dataclass(frozen=True)
class InstallResult:
    """Where an install put the skill."""

    namespace: str
    slug: str
    installed_targets: tuple[Target, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``install`` answer from the CLI's decoded JSON."""
        try:
            return cls(
                namespace=payload["namespace"],
                slug=payload["slug"],
                installed_targets=_parse_targets(payload, "installed"),
            )
        except (KeyError, TypeError) as unusable:
            raise MalformedAnswerError(f"unusable install answer: {unusable}") from unusable


@dataclass(frozen=True)
class UninstallResult:
    """What an uninstall took away."""

    removed_targets: tuple[Target, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build one ``remove`` answer from the CLI's decoded JSON."""
        try:
            return cls(removed_targets=_parse_targets(payload, "removed"))
        except (KeyError, TypeError) as unusable:
            raise MalformedAnswerError(f"unusable remove answer: {unusable}") from unusable


def _parse_targets(payload: dict[str, Any], action: TargetAction) -> tuple[Target, ...]:
    """Read the payload's ``installed`` or ``removed`` list into targets."""
    return tuple(Target.from_payload(e) for e in payload[action])
