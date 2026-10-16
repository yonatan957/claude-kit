"""The one place an install or a removal touched."""

from dataclasses import dataclass
from typing import Any, Self

from skillhub_library.errors import MalformedAnswerError

__all__ = ["Target"]


@dataclass(frozen=True)
class Target:
    """One location on computer a skill was installed to or removed from.

    ``agent`` and ``directory`` say which place, and every target has them.
    ``remove`` adds ``namespace`` and ``existed``; those keep their defaults on
    an install, which is why they are the only two that have any.
    """

    agent: str
    directory: str  # the CLI's "dir"
    namespace: str = ""
    existed: bool | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build from one element of the CLI's ``installed``/``removed`` list."""
        try:
            return cls(
                agent=payload["agent"],
                directory=payload["dir"],
                namespace=payload.get("namespace", ""),
                existed=payload.get("existed"),
            )
        except (KeyError, TypeError) as unusable:
            raise MalformedAnswerError(f"unusable target: {unusable}") from unusable
