"""``ck list``: the components the kit has installed."""

import sqlite3
from pathlib import Path

from claude_kit import storage
from claude_kit.components import ComponentKind, InstalledComponent
from claude_kit.helpers import CLAUDE_KIT_HOME, DATABASE_FILE_NAME, KitNotFound

__all__ = ["get_installed_components"]


def get_installed_components(
    kind: ComponentKind | None = None,
    home: Path | None = None,
) -> list[InstalledComponent]:
    connection = _connect_db(home)
    try:
        return storage.get_installed_components(connection, kind)
    finally:
        connection.close()


def _connect_db(home: Path | None = None) -> sqlite3.Connection:
    home = home or CLAUDE_KIT_HOME
    database = home / DATABASE_FILE_NAME
    if not database.exists():
        raise KitNotFound(home)
    return storage.connect(database)
