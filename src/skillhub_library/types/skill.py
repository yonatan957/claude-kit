from dataclasses import dataclass
from typing import Any, Self

from ..errors import MalformedAnswerError

__all__ = ["Skill"]


@dataclass(frozen=True)
class Skill:
    """
    ``namespace`` is the account that published it -- the shared public one is
    ``"global"`` -- and ``slug`` is the skill's own id inside it. Both go back
    to :meth:`~.SkillHubClient.install` as they are: the CLI keeps them apart.
    Neither has a default: a hit that cannot say which skill it is is not a hit.
    """

    namespace: str
    slug: str
    latest_version: str = ""
    summary: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build from one element of the CLI's ``items`` list."""
        try:
            return cls(
                namespace=payload["namespace"],
                slug=payload["slug"],
                latest_version=payload.get("latestVersion", ""),
                summary=payload.get("summary", ""),
            )
        except (KeyError, TypeError) as unusable:
            raise MalformedAnswerError(f"unusable search hit: {unusable}") from unusable
