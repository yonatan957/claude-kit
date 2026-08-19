from claude_kit.components import ClaudeComponent, ComponentKind
from skillhub_library import SkillHubClient

from .source import Source

__all__ = ["SkillHubSource"]


class SkillHubSource(Source):

    def __init__(self, client: SkillHubClient | None = None) -> None:
        self.client = client or SkillHubClient()

    @property
    def name(self) -> str:
        return "skillhub"

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        match kind:
            case ComponentKind.SKILL:
                raise NotImplementedError
            case _:
                return []

    def install(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        match kind:
            case ComponentKind.SKILL:
                raise NotImplementedError
            case _:
                return []

    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        match kind:
            case ComponentKind.SKILL:
                raise NotImplementedError
            case _:
                return []
