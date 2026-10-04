"""``ck list``: the components the kit has installed."""

from pathlib import Path

from claude_kit import storage
from claude_kit.components import ComponentKind, InstalledComponent

__all__ = ["get_installed_components"]


def get_installed_components(
    kind: ComponentKind | None = None,
    home: Path | None = None,
) -> list[InstalledComponent]:
    connection = storage.open_kit_database(home)
    try:
        return storage.get_installed_components(connection, kind)
    finally:
        connection.close()
