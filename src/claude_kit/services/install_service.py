from datetime import datetime, timezone
from pathlib import Path

from claude_kit import storage
from claude_kit.components import ClaudeComponent, ComponentKind, InstalledComponent
from claude_kit.helpers import Conflict
from claude_kit.sources import AVAILABLE_SOURCES, Source

__all__ = ["install"]


def install(
    kind: ComponentKind,
    name: str,
    sources: list[Source] | None = None,
    home: Path | None = None,
) -> list[ClaudeComponent]:
    sources = AVAILABLE_SOURCES if sources is None else sources
    connection = storage.open_kit_database(home)
    try:
        recorded = storage.find_components_by_name(connection, kind, name)
        if recorded:
            source = recorded[0].component.source
            raise Conflict(f"{kind} {name!r} is already installed from {source}")

        for source in sources:
            installed = source.install(kind, name)
            if installed:
                installed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                for component in installed:
                    storage.add_component(
                        connection,
                        InstalledComponent(component=component, installed_at=installed_at),
                    )
                return installed
        return []
    finally:
        connection.close()
