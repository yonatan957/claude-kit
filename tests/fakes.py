from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import CLAUDE_BINARY, CommandResult
from claude_kit.sources import Source
from claude_kit.sources.genie.manifest import GenieInput
from skillhub_library.types import InstallResult, SearchResult, UninstallResult

__all__ = [
    "FakeCall",
    "FakePrompter",
    "FakeRunner",
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


@dataclass(frozen=True)
class FakeCall:
    command: list[str]
    env: Mapping[str, str] | None
    label: str


class FakeRunner:
    """Stands in for ``run``: ``claude mcp`` answers from a set of registered names,
    and scripts succeed. ``failing`` maps a claude action or a script's file name to
    the stderr it fails with instead."""

    def __init__(
        self,
        registered: Iterable[str] = (),
        failing: Mapping[str, str] | None = None,
        claude_missing: bool = False,
    ) -> None:
        self.registered = set(registered)
        self.failing = dict(failing or {})
        self.claude_missing = claude_missing
        self.calls: list[FakeCall] = []

    def __call__(
        self,
        command: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        label: str | None = None,
    ) -> CommandResult:
        label = label or " ".join(command)
        self.calls.append(FakeCall(list(command), env, label))
        return self._answer(list(command), label)

    @property
    def steps(self) -> list[str]:
        return [_step(call.command) for call in self.calls]

    def _answer(self, command: list[str], label: str) -> CommandResult:
        step = _step(command)
        failure = self.failing.get(Path(command[-1]).name) or self.failing.get(step)
        if command[0] == CLAUDE_BINARY and self.claude_missing:
            return CommandResult(label, 127, stderr="claude: not found")
        if failure:
            return CommandResult(label, 1, stderr=failure)
        if command[0] != CLAUDE_BINARY:
            return CommandResult(label, 0)

        name = command[3]
        absent = CommandResult(label, 1, stderr=f'No MCP server named "{name}"')
        if step == "get":
            return CommandResult(label, 0) if name in self.registered else absent
        if step == "remove":
            if name not in self.registered:
                return absent
            self.registered.remove(name)
            return CommandResult(label, 0)
        self.registered.add(name)
        return CommandResult(label, 0)


def _step(command: list[str]) -> str:
    """The ``claude mcp`` action, or the script's name without its suffix."""
    if command[0] == CLAUDE_BINARY:
        return command[2]
    return Path(command[-1]).stem


class FakePrompter:
    def __init__(self, answers: Mapping[str, str] | None = None) -> None:
        self.answers = dict(answers or {})
        self.asked: list[tuple[str, str | None]] = []

    def __call__(self, question: GenieInput, current: str | None) -> str:
        self.asked.append((question.key, current))
        return self.answers.get(question.key, "")
