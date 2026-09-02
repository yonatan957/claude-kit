"""``ck uninstall``: take a component back out, from one source or from whichever has it."""

from claude_kit.components import ClaudeComponent
from claude_kit.sources import AVAILABLE_SOURCES, Source, get_source

__all__ = ["uninstall"]


def uninstall(
    component: ClaudeComponent,
    sources: list[Source] | None = None,
) -> list[ClaudeComponent]:
    sources = AVAILABLE_SOURCES if sources is None else sources

    if component.source:
        source = get_source(component.source, sources)
        return source.uninstall(component.kind, component.name)

    for source in sources:
        removed = source.uninstall(component.kind, component.name)
        if removed:
            return removed
    return []
