from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.sources import AVAILABLE_SOURCES, Source

__all__ = ["search"]


def search(
    kind: ComponentKind,
    query: str = "",
    sources: list[Source] | None = None,
) -> list[ClaudeComponent]:

    sources = AVAILABLE_SOURCES if sources is None else sources
    found: list[ClaudeComponent] = []
    for source in sources:
        found.extend(source.search(kind, query))
    return found
