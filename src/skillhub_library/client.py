"""The entry point: one client that searches the registry and manages installs."""

import json

from ._cli import TIMEOUT, run
from .dtos import InstallRequest, SearchRequest, UninstallRequest
from .types import (
    AgentSpec,
    Directory,
    InstallResult,
    Scope,
    SearchResult,
    UninstallResult,
)

__all__ = ["SkillHubClient"]


class SkillHubClient:
    """Talks to one registry with one set of credentials.

        client = SkillHubClient(token="...")
        client.install("pdf-parser", agent="claude-code", scope="user")

    ``registry``, ``token`` and ``timeout`` are settled once here so the
    commands themselves only take what varies between calls. Each command
    builds the matching request from :mod:`skillhub_library.dtos`, runs it, and
    hands the decoded answer to the result type: the request owns the argv,
    :func:`~._cli.run` owns the process, the client turns stdout into JSON, and
    the result owns the shape it reads there.
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
        return SearchResult.from_payload(json.loads(stdout))

    def install(
        self,
        slug: str,
        *,
        namespace: str | None = None,
        agent: AgentSpec | None = None,
        scope: Scope | None = None,
        directory: Directory | None = None,
        force: bool = False,
    ) -> InstallResult:
        """Install a skill.

        ``slug`` and ``namespace`` are a search hit's own two fields; leaving
        ``namespace`` out installs from the CLI's default, ``global``. ``agent``
        may be one profile name or a list of them. ``directory`` installs to a
        custom path and cannot be combined with ``scope`` or ``agent``.
        """
        request = InstallRequest(
            slug=slug,
            namespace=namespace,
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
        return InstallResult.from_payload(json.loads(stdout))

    def uninstall(
        self,
        slug: str,
        *,
        agent: AgentSpec | None = None,
        all_targets: bool = False,
    ) -> UninstallResult:
        """Remove an installed skill (the CLI's ``remove``).

        The slug matches installations across namespaces; ``all_targets``
        removes every target without prompting.
        """
        request = UninstallRequest(slug=slug, agent=agent, all_targets=all_targets)
        stdout = run(
            request.to_args(registry=self.registry, token=self.token),
            timeout=self.timeout,
            label=request.label,
        )
        return UninstallResult.from_payload(json.loads(stdout))
