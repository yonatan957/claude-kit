"""SkillHub, reached through its CLI, as one of the kit's sources."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import SourceError, SourceUnreachable
from claude_kit.sources.source import Source
from skillhub_library import SkillHubClient
from skillhub_library.errors import (
    CLINotFoundError,
    CLITimeoutError,
    CommandError,
    SkillHubError,
)
from skillhub_library.types import Skill

__all__ = ["SkillHubSource"]

#: The CLI has no code for "no such skill" -- a missing slug comes back as a
#: failure envelope like any other. These are the words it uses for one, in the
#: message and in the registry's own error nested under ``details``.
_MISSING_WORDS = ("not found", "notfound")


class SkillHubSource(Source):
    kinds = frozenset({ComponentKind.SKILL})

    def __init__(
        self, registry: str | None = None, client: SkillHubClient | None = None
    ) -> None:
        self.registry = registry
        self.client = client or SkillHubClient(registry=registry)

    @property
    def name(self) -> str:
        return "skillhub"

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        try:
            found = self.client.search(query)
        except SkillHubError as failure:
            if _is_missing(failure):
                return []
            raise self._to_source_error(failure) from failure
        return [self._to_component(kind, skill) for skill in found]

    def install(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        try:
            installed = self.client.install(name)
        except SkillHubError as failure:
            if _is_missing(failure):
                return []
            raise self._to_source_error(failure) from failure
        return [
            ClaudeComponent(
                kind=kind,
                name=installed.slug or name,
                source=self.name,
                tag=installed.namespace,
            )
        ]

    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        try:
            removed = self.client.uninstall(name, all_targets=True)
        except SkillHubError as failure:
            if _is_missing(failure):
                return []
            raise self._to_source_error(failure) from failure
        return [
            ClaudeComponent(
                kind=kind, name=name, source=self.name, tag=target.namespace
            )
            for target in removed.removed_targets
            if target.existed is not False
        ]

    def _to_source_error(self, failure: SkillHubError) -> SourceError:
        if isinstance(failure, (CLINotFoundError, CLITimeoutError)):
            return SourceUnreachable(self.name, str(failure))
        return SourceError(self.name, str(failure))

    def _to_component(self, kind: ComponentKind, skill: Skill) -> ClaudeComponent:
        return ClaudeComponent(
            kind=kind,
            name=skill.slug,
            source=self.name,
            description=skill.summary,
            version=skill.latest_version,
            tag=skill.namespace,
        )


def _is_missing(failure: SkillHubError) -> bool:
    """Whether the CLI reported "no such skill", which is an answer and not a
    failure: it is what lets the caller go on to ask the next source."""
    if not isinstance(failure, CommandError):
        return False
    reported = f"{failure.message} {failure.details}".casefold()
    return any(word in reported for word in _MISSING_WORDS)
