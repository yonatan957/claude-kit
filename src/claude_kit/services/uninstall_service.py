"""``ck uninstall``: take a component back out, from one source or from whichever has it."""

from pathlib import Path

from claude_kit import storage
from claude_kit.components import ClaudeComponent
from claude_kit.sources import AVAILABLE_SOURCES, Source, get_source

__all__ = ["uninstall"]


def uninstall(
    component: ClaudeComponent,
    sources: list[Source] | None = None,
    home: Path | None = None,
) -> list[ClaudeComponent]:
    sources = AVAILABLE_SOURCES if sources is None else sources
    connection = storage.open_kit_database(home)
    try:
        removed = _uninstall_from_sources(component, sources)
        for one in removed:
            storage.remove_components(connection, one.kind, one.name, one.tag)
        return removed
    finally:
        connection.close()


def _uninstall_from_sources(
    component: ClaudeComponent,
    sources: list[Source],
) -> list[ClaudeComponent]:
    if component.source:
        source = get_source(component.source, sources)
        return source.uninstall(component.kind, component.name)

    for source in sources:
        removed = source.uninstall(component.kind, component.name)
        if removed:
            return removed
    return []
