"""``ck install``: the first source that has it."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.sources import AVAILABLE_SOURCES, Source

__all__ = ["install"]


def install(
    kind: ComponentKind,
    name: str,
    sources: list[Source] | None = None,
) -> list[ClaudeComponent]:
    
    sources = AVAILABLE_SOURCES if sources is None else sources
    for source in sources:
        installed = source.install(kind, name)
        if installed:
            return installed
    return []
