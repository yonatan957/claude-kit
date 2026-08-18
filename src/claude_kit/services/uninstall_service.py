"""``ck uninstall``: straight to the source when we know it."""

from claude_kit.components import ClaudeComponent
from claude_kit.sources import AVAILABLE_SOURCES, Source, source_by_name

__all__ = ["UninstallService"]


class UninstallService:
    """Removes a component from the source it came from.

    A component that names its source is removed there and nowhere else.
    One that does not -- a bare name off the command line -- sends us through
    the sources in order until one of them has something to remove.
    """

    def __init__(self, sources: list[Source] | None = None) -> None:
        self.sources = AVAILABLE_SOURCES if sources is None else sources

    def uninstall(self, component: ClaudeComponent) -> list[ClaudeComponent]:
        """Remove ``component``, and answer with what was removed."""
        if component.source:
            source = source_by_name(component.source, self.sources)
            return source.uninstall(component.kind, component.name) if source else []

        for source in self.sources:
            removed = source.uninstall(component.kind, component.name)
            if removed:
                return removed
        return []
