"""What ``install`` and ``uninstall`` answer with."""

import json
from dataclasses import dataclass, field
from typing import Self

from .aliases import JSONObject
from .targets import Target

__all__ = ["InstallResult", "RemoveResult"]


@dataclass(frozen=True)
class InstallResult:
    """Where an install put the skill."""

    namespace: str = ""
    slug: str = ""
    installed: tuple[Target, ...] = ()
    raw: JSONObject = field(default_factory=dict)

    @classmethod
    def from_payload(cls, text: str) -> Self:
        """Decode one ``install`` answer straight from the CLI's stdout."""
        payload = json.loads(text)
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
    raw: JSONObject = field(default_factory=dict)

    @classmethod
    def from_payload(cls, text: str) -> Self:
        """Decode one ``remove`` answer straight from the CLI's stdout."""
        payload = json.loads(text)
        return cls(
            scope=payload.get("scope", ""),
            removed=_targets(payload, "removed"),
            raw=payload,
        )


def _targets(payload: JSONObject, key: str) -> tuple[Target, ...]:
    entries = payload.get(key)
    return tuple(Target.from_object(e) for e in entries) if isinstance(entries, list) else ()
