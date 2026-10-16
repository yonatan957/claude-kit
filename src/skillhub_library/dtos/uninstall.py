"""The ``uninstall`` request -- the CLI spells the command ``remove``."""

from dataclasses import dataclass

from skillhub_library.types import AgentSpec
from skillhub_library.dtos._encode import connection, repeated, switch
from skillhub_library.dtos.base import Request

__all__ = ["UninstallRequest"]


@dataclass(frozen=True)
class UninstallRequest(Request):
    """Remove one skill's local installs.

    ``slug`` alone is what the CLI takes: a local removal matches by slug
    across namespaces. (The CLI's ``--namespace`` narrows a *remote* delete,
    which this library does not do.) ``all_targets`` removes every target
    without prompting.
    """

    slug: str
    agent: AgentSpec | None = None
    all_targets: bool = False

    def to_args(self, *, registry: str | None = None, token: str | None = None) -> list[str]:
        return [
            "remove",
            self.slug,
            *connection(registry, token),
            *repeated("--agent", self.agent),
            *switch("--all", self.all_targets),
        ]

    @property
    def label(self) -> str:
        return f"remove {self.slug}"
