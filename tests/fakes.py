from collections.abc import Iterable
from dataclasses import replace
from typing import Any

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.sources import Source
from skillhub_library.types import InstallResult, SearchResult, UninstallResult

__all__ = [
    "FakeSkillHubClient",
    "FakeSource",
    "install_payload",
    "search_payload",
    "skill_payload",
    "uninstall_payload",
]


class FakeSource(Source):

    def __init__(
        self,
        name: str,
        components: Iterable[ClaudeComponent] = (),
        kinds: Iterable[ComponentKind] | None = None,
        failure: Exception | None = None,
    ) -> None:
        self._name = name
        self.components = list(components)
        self.kinds = frozenset(ComponentKind if kinds is None else kinds)
        self.failure = failure
        self.searched: list[tuple[ComponentKind, str]] = []
        self.installed: list[tuple[ComponentKind, str]] = []
        self.uninstalled: list[tuple[ComponentKind, str]] = []
        self.forced: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        self.searched.append((kind, query))
        if self.failure:
            raise self.failure
        return [
            self._as_mine(component)
            for component in self.components
            if component.kind == kind and query in component.name
        ]

    def install(
        self, kind: ComponentKind, name: str, force: bool = False
    ) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        self.installed.append((kind, name))
        if force:
            self.forced.append(name)
        if self.failure:
            raise self.failure
        return self._find_components_by_name(kind, name)

    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        self.uninstalled.append((kind, name))
        if self.failure:
            raise self.failure
        return self._find_components_by_name(kind, name)

    def _find_components_by_name(
        self, kind: ComponentKind, name: str
    ) -> list[ClaudeComponent]:
        return [
            self._as_mine(component)
            for component in self.components
            if component.kind == kind and component.name == name
        ]

    def _as_mine(self, component: ClaudeComponent) -> ClaudeComponent:
        """Every real source stamps its own name on what it answers with."""
        return replace(component, source=self._name)


class FakeSkillHubClient:

    def __init__(
        self,
        search: Any = None,
        install: Any = None,
        uninstall: Any = None,
    ) -> None:
        self._search = search
        self._install = install
        self._uninstall = uninstall
        self.calls: list[str] = []

    def search(self, query: str = "", **_: Any) -> SearchResult:
        self.calls.append("search")
        return _answer(self._search)

    def install(self, slug: str, **_: Any) -> InstallResult:
        self.calls.append("install")
        return _answer(self._install)

    def uninstall(self, slug: str, **_: Any) -> UninstallResult:
        self.calls.append("uninstall")
        return _answer(self._uninstall)


def _answer(value: Any) -> Any:
    if isinstance(value, Exception):
        raise value
    return value


def skill_payload(
    namespace: str = "global",
    slug: str = "code-reviewer",
    latest_version: str = "1.2.0",
    summary: str = "Reviews code carefully",
) -> dict[str, Any]:
    return {
        "namespace": namespace,
        "slug": slug,
        "latestVersion": latest_version,
        "summary": summary,
    }


def search_payload(*skills: dict[str, Any]) -> SearchResult:
    return SearchResult.from_payload({"items": list(skills), "total": len(skills)})


def install_payload(
    namespace: str = "global",
    slug: str = "code-reviewer",
    agent: str = "claude-code",
    directory: str = "~/.claude/skills/code-reviewer",
) -> InstallResult:
    return InstallResult.from_payload(
        {
            "namespace": namespace,
            "slug": slug,
            "installed": [{"agent": agent, "dir": directory}],
        }
    )


def uninstall_payload(*removed: dict[str, Any]) -> UninstallResult:
    return UninstallResult.from_payload({"removed": list(removed)})
