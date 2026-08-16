"""What ``install`` and ``uninstall`` answer with."""

from __future__ import annotations

from dataclasses import dataclass, field

from .aliases import JSONObject, Payload
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
    def from_payload(cls, payload: Payload) -> InstallResult:
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
    raw: JSONObject = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Payload) -> RemoveResult:
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            scope=payload.get("scope", ""),
            removed=_targets(payload, "removed"),
            raw=payload,
        )


def _targets(payload: JSONObject, key: str) -> tuple[Target, ...]:
    entries = payload.get(key)
    return tuple(Target.from_payload(e) for e in entries) if isinstance(entries, list) else ()
