"""The entry point: one client that searches the registry and manages installs."""

from collections.abc import Sequence

from ._cli import TIMEOUT, flags, run
from .types import (
    AgentSpec,
    Directory,
    FlagValue,
    InstallResult,
    Payload,
    RemoveResult,
    Scope,
    SearchResult,
)

__all__ = ["SkillHubClient"]


class SkillHubClient:
    """Talks to one registry with one set of credentials.

        client = SkillHubClient(token="...")
        client.install("pdf-parser", agent="claude-code", scope="user")

    ``registry``, ``token`` and ``timeout`` are settled once here so the
    commands themselves only take what varies between calls.
    """

    def __init__(
        self,
        *,
        registry: str | None = None,
        token: str | None = None,
        timeout: float = TIMEOUT,
    ) -> None:
        self.registry = registry
        self.token = token
        self.timeout = timeout

    def __repr__(self) -> str:
        token = "***" if self.token else None  # never echo the credential
        return f"{type(self).__name__}(registry={self.registry!r}, token={token!r})"

    def search(self, query: str = "", *, limit: int | None = None) -> SearchResult:
        """Search published skills. An empty ``query`` lists everything."""
        search_result = self._run(["search", query], limit=limit)
        return SearchResult.from_payload(search_result)

    def install(
        self,
        name: str,
        *,
        version: str | None = None,
        agent: AgentSpec | None = None,
        scope: Scope | None = None,
        directory: Directory | None = None,
        force: bool = False,
    ) -> InstallResult:
        """Install a skill.

        ``name`` is ``slug``, ``team/slug``, ``@team/slug`` or ``team--slug``;
        :attr:`~.Skill.name` gives the namespaced form of a search hit. ``agent``
        may be one profile name or a list of them. ``directory`` installs to a
        custom path and cannot be combined with ``scope`` or ``agent``.
        """
        payload = self._run(
            ["install", name],
            version=version,
            scope=scope,
            agent=agent,
            dir=directory,
            force=force,
        )
        return InstallResult.from_payload(payload)

    def uninstall(
        self,
        name: str,
        *,
        agent: AgentSpec | None = None,
        all_targets: bool = False,
    ) -> RemoveResult:
        """Remove an installed skill (the CLI's ``remove``).

        A bare slug removes matching installations across namespaces; pass the
        namespaced ``team/slug`` to narrow it to one. ``all_targets`` removes
        every target without prompting.
        """
        payload = self._run(["remove", name], agent=agent, all=all_targets)
        return RemoveResult.from_payload(payload)

    def _run(self, command: Sequence[str], **options: FlagValue) -> Payload:
        """Run ``command`` with this client's registry, token and timeout."""
        args = [*command, *flags(registry=self.registry, token=self.token, **options)]
        return run(args, timeout=self.timeout)
