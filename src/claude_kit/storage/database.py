"""Opening ``installed.db`` and giving it the shape ``schema.py`` describes."""

import sqlite3
from pathlib import Path

from claude_kit.storage.schema import SCHEMA_STATEMENTS, SCHEMA_VERSION

__all__ = ["connect", "ensure_schema", "get_schema_version"]


def connect(path: Path | str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION:d}")


def get_schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])
