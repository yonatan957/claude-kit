"""One published skill, as ``search`` describes it."""

from dataclasses import dataclass
from typing import Any, Self

__all__ = ["Skill"]


@dataclass(frozen=True)
class Skill:
    """One search hit.

    ``namespace`` is the account that published it -- the shared public one is
    ``"global"`` -- and ``slug`` is the skill's own id inside it. Both go back
    to :meth:`~.SkillHubClient.install` as they are: the CLI keeps them apart.
    """

    namespace: str = ""
    slug: str = ""
    latest_version: str = ""
    summary: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build from one element of the CLI's ``items`` list."""
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            namespace=payload.get("namespace", ""),
            slug=payload.get("slug", ""),
            latest_version=payload.get("latestVersion", ""),
            summary=payload.get("summary", ""),
        )
