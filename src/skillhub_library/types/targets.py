"""The one place an install or a removal touched."""

from dataclasses import dataclass
from typing import Any, Self

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

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build from one element of the CLI's ``installed``/``removed`` list."""
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            agent=payload.get("agent", ""),
            directory=payload.get("dir", ""),
            namespace=payload.get("namespace", ""),
            existed=payload.get("existed"),
        )
