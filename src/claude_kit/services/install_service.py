"""``ck install``: the first source that has it."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.sources import AVAILABLE_SOURCES, Source

__all__ = ["InstallService"]


class InstallService:
    """Asks each source in turn and stops at the first one that installs.

    A source that does not have the package answers empty, which is not a
    failure -- it is simply the next source's turn.
    """

    def __init__(self, sources: list[Source] | None = None) -> None:
        self.sources = AVAILABLE_SOURCES if sources is None else sources

    def install(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        """Install ``name`` from the first source that has it.

        Answers with what that source installed, or empty when no source did.
        """
        for source in self.sources:
            installed = source.install(kind, name)
            if installed:
                return installed
        return []
