from claude_kit.components import ClaudeComponent
from claude_kit.sources import AVAILABLE_SOURCES, Source, source_by_name

__all__ = ["uninstall"]


def uninstall(
    component: ClaudeComponent,
    sources: list[Source] | None = None,
) -> list[ClaudeComponent]:

    sources = AVAILABLE_SOURCES if sources is None else sources

    if component.source:
        source = source_by_name(component.source, sources)
        return source.uninstall(component.kind, component.name) if source else []

    for source in sources:
        removed = source.uninstall(component.kind, component.name)
        if removed:
            return removed
    return []
