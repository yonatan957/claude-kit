"""The ``install`` request."""

from dataclasses import dataclass

from ..types import AgentSpec, Directory, Scope
from ._encode import connection, option, path, repeated, switch
from .base import Request

__all__ = ["InstallRequest"]


@dataclass(frozen=True)
class InstallRequest(Request):
    """Install one skill.

    ``slug`` is the skill's own id and ``namespace`` is the account that
    published it -- the CLI takes them as two arguments and defaults the
    namespace to ``global``, so a search hit's two fields go in unchanged.
    ``agent`` may be one profile name or a list of them.
    """

    slug: str
    namespace: str | None = None
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
            self.slug,
            *connection(registry, token),
            *option("--namespace", self.namespace),
            *option("--scope", self.scope),
            *repeated("--agent", self.agent),
            *path("--dir", self.directory),
            *switch("--force", self.force),
        ]

    @property
    def label(self) -> str:
        return f"install {self.slug}"
