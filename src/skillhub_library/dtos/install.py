"""The ``install`` request."""

from dataclasses import dataclass

from ..types import AgentSpec, Directory, Scope
from ._encode import connection, option, path, repeated, switch
from .base import Request

__all__ = ["InstallRequest"]


@dataclass(frozen=True)
class InstallRequest(Request):
    """Install one skill.

    ``name`` is ``slug``, ``team/slug``, ``@team/slug`` or ``team--slug``.
    ``agent`` may be one profile name or a list of them.
    """

    name: str
    version: str | None = None
    agent: AgentSpec | None = None
    scope: Scope | None = None
    directory: Directory | None = None
    force: bool = False

    def __post_init__(self) -> None:
        # The CLI rejects this pairing; catching it here costs a round trip
        # less and says which two options are fighting.
        if self.directory is not None and (self.scope is not None or self.agent is not None):
            raise ValueError(
                "directory installs to a path of its own and cannot be combined "
                "with scope or agent"
            )

    def to_args(self, *, registry: str | None = None, token: str | None = None) -> list[str]:
        return [
            "install",
            self.name,
            *connection(registry, token),
            *option("--version", self.version),
            *option("--scope", self.scope),
            *repeated("--agent", self.agent),
            *path("--dir", self.directory),
            *switch("--force", self.force),
        ]

    @property
    def label(self) -> str:
        return f"install {self.name}"
