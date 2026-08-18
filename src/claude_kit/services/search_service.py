"""``ck search``: every source at once."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.sources import AVAILABLE_SOURCES, Source

__all__ = ["SearchService"]


class SearchService:
    """Collects hits from every source.

    Nothing is dropped and nothing wins: a package published in two places
    shows up twice, each hit naming the source it came from.
    """

    def __init__(self, sources: list[Source] | None = None) -> None:
        self.sources = AVAILABLE_SOURCES if sources is None else sources

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        """Every component of ``kind`` matching ``query``, from all sources."""
        found: list[ClaudeComponent] = []
        for source in self.sources:
            found.extend(source.search(kind, query))
        return found
