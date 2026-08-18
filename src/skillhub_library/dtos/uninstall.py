"""The ``uninstall`` request -- the CLI spells the command ``remove``."""

from dataclasses import dataclass

from ..types import AgentSpec
from ._encode import connection, repeated, switch
from .base import Request

__all__ = ["UninstallRequest"]


@dataclass(frozen=True)
class UninstallRequest(Request):
    """Remove an installed skill.

    A bare slug removes matching installations across namespaces; pass the
    namespaced ``team/slug`` to narrow it to one. ``all_targets`` removes every
    target without prompting.
    """

    name: str
    agent: AgentSpec | None = None
    all_targets: bool = False

    def to_args(self, *, registry: str | None = None, token: str | None = None) -> list[str]:
        return [
            "remove",
            self.name,
            *connection(registry, token),
            *repeated("--agent", self.agent),
            *switch("--all", self.all_targets),
        ]

    @property
    def label(self) -> str:
        return f"remove {self.name}"
