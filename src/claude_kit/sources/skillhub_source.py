from collections.abc import Iterator
from contextlib import contextmanager

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import SourceError
from claude_kit.sources.source import Source
from skillhub_library import SkillHubClient
from skillhub_library.errors import SkillHubError
from skillhub_library.types import Skill

__all__ = ["SkillHubSource"]


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
        with _as_source_error(self.name):
            found = self.client.search(query)
        return [self._to_component(kind, skill) for skill in found]

    def install(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        with _as_source_error(self.name):
            installed = self.client.install(name)
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
        with _as_source_error(self.name):
            removed = self.client.uninstall(name, all_targets=True)
        return [
            ClaudeComponent(
                kind=kind, name=name, source=self.name, tag=target.namespace
            )
            for target in removed.removed_targets
            if target.existed is not False
        ]

    def _to_component(self, kind: ComponentKind, skill: Skill) -> ClaudeComponent:
        return ClaudeComponent(
            kind=kind,
            name=skill.slug,
            source=self.name,
            description=skill.summary,
            version=skill.latest_version,
            tag=skill.namespace,
        )


@contextmanager
def _as_source_error(source: str) -> Iterator[None]:
    """A source speaks claude-kit's errors, not its client library's."""
    try:
        yield
    except SkillHubError as failure:
        raise SourceError(source, str(failure)) from failure
