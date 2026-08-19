"""The one place an install or a removal touched."""

from dataclasses import dataclass, field
from typing import Self

from skillhub_library.types.aliases import JSONObject, Payload

__all__ = ["Target"]


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
    raw: JSONObject = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Payload) -> Self:
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            agent=payload.get("agent", ""),
            directory=payload.get("dir", ""),
            namespace=payload.get("namespace", ""),
            existed=payload.get("existed"),
            raw=payload,
        )
