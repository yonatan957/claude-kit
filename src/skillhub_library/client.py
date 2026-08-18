"""The entry point: one client that searches the registry and manages installs."""

from ._cli import TIMEOUT, run
from .dtos import InstallRequest, SearchRequest, UninstallRequest
from .types import (
    AgentSpec,
    Directory,
    InstallResult,
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
    commands themselves only take what varies between calls. Each command
    builds the matching request from :mod:`skillhub_library.dtos`, runs it, and
    hands the answer to the result type: the request owns the argv,
    :func:`~._cli.run` owns the process, and the result owns how to read the
    stdout it comes back as.
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
        request = SearchRequest(query=query, limit=limit)
        stdout = run(
            request.to_args(registry=self.registry, token=self.token),
            timeout=self.timeout,
            label=request.label,
        )
        return SearchResult.from_payload(stdout)

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
        request = InstallRequest(
            name=name,
            version=version,
            agent=agent,
            scope=scope,
            directory=directory,
            force=force,
        )
        stdout = run(
            request.to_args(registry=self.registry, token=self.token),
            timeout=self.timeout,
            label=request.label,
        )
        return InstallResult.from_payload(stdout)

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
        request = UninstallRequest(name=name, agent=agent, all_targets=all_targets)
        stdout = run(
            request.to_args(registry=self.registry, token=self.token),
            timeout=self.timeout,
            label=request.label,
        )
        return RemoveResult.from_payload(stdout)
