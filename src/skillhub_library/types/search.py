"""What ``search`` answers with."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Self

from .aliases import JSONObject, Payload

__all__ = ["Skill", "SearchResult"]


@dataclass(frozen=True)
class Skill:
    """One search hit."""

    namespace: str = ""
    slug: str = ""
    latest_version: str = ""
    summary: str = ""
    raw: JSONObject = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Payload) -> Self:
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            namespace=payload.get("namespace", ""),
            slug=payload.get("slug", ""),
            latest_version=payload.get("latestVersion", ""),
            summary=payload.get("summary", ""),
            raw=payload,
        )

    @property
    def name(self) -> str:
        """What ``install``/``uninstall`` take: ``namespace/slug``, else the slug.

        The slug alone matches the skill in every namespace that publishes it, so
        this is what you want whenever you mean *this* hit and no other.
        """
        return f"{self.namespace}/{self.slug}" if self.namespace else self.slug


@dataclass(frozen=True)
class SearchResult:
    """Iterates and ``len()``s like a list of :class:`Skill`, but keeps ``total``."""

    items: tuple[Skill, ...] = ()
    total: int = 0

    @classmethod
    def from_payload(cls, payload: Payload) -> Self:
        payload = payload if isinstance(payload, dict) else {}
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
