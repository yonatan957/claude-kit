"""Changes made to ``installed.db``; timestamps and tags come from the caller."""

import sqlite3
from collections.abc import Mapping

from claude_kit.components import ComponentKind
from claude_kit.components.installed_component import ComponentConfig, InstalledComponent
from claude_kit.storage.schema import COMPONENT_COLUMNS, name_filter

__all__ = [
    "add_component",
    "remove_components",
    "set_component_config",
    "set_component_enabled",
]

_INSERT = (
    f"INSERT INTO installed_components ({', '.join(COMPONENT_COLUMNS)})"
    f" VALUES ({', '.join('?' * len(COMPONENT_COLUMNS))})"
)


def add_component(
    connection: sqlite3.Connection,
    installed: InstalledComponent,
    *,
    replace: bool = False,
) -> None:
    component = installed.component
    with connection:
        if replace:
            _delete_components(connection, component.kind, component.name, component.tag)
        component_id = connection.execute(_INSERT, _to_column_values(installed)).lastrowid
        _insert_config_keys(connection, int(component_id or 0), installed.config.keys)


def remove_components(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str = "",
) -> int:
    with connection:
        return _delete_components(connection, kind, name, tag)


def set_component_config(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str,
    config: ComponentConfig,
) -> int:
    with connection:
        ids = _find_ids_by_name(connection, kind, name, tag)
        for component_id in ids:
            connection.execute(
                "UPDATE installed_components"
                "   SET config_status = ?, config_verified_at = ?"
                " WHERE id = ?",
                (str(config.status), _or_null(config.verified_at), component_id),
            )
            connection.execute(
                "DELETE FROM component_config_keys WHERE component_id = ?",
                (component_id,),
            )
            _insert_config_keys(connection, component_id, config.keys)
        return len(ids)


def set_component_enabled(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str,
    enabled: bool,
) -> int:
    where, parameters = name_filter(kind, name, tag)
    with connection:
        return connection.execute(
            f"UPDATE installed_components SET enabled = ? {where}",
            [int(enabled), *parameters],
        ).rowcount


def _or_null(value: str) -> str | None:
    return value or None


def _to_column_values(installed: InstalledComponent) -> tuple[str | int | None, ...]:
    component = installed.component
    values: dict[str, str | int | None] = {
        "kind": str(component.kind),
        "name": component.name,
        "tag": component.tag,
        "source": component.source,
        "description": component.description,
        "version": component.version,
        "installed_hash": installed.installed_hash,
        "installed_at": installed.installed_at,
        "updated_at": _or_null(installed.updated_at),
        "marketplace": _or_null(installed.marketplace),
        "enabled": int(installed.enabled),
        "config_status": str(installed.config.status),
        "config_verified_at": _or_null(installed.config.verified_at),
    }
    return tuple(values[column] for column in COMPONENT_COLUMNS)


def _delete_components(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str,
) -> int:
    where, parameters = name_filter(kind, name, tag)
    statement = f"DELETE FROM installed_components {where}"
    return connection.execute(statement, parameters).rowcount


def _find_ids_by_name(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str,
) -> list[int]:
    where, parameters = name_filter(kind, name, tag)
    statement = f"SELECT id FROM installed_components {where}"
    return [row["id"] for row in connection.execute(statement, parameters)]


def _insert_config_keys(
    connection: sqlite3.Connection,
    component_id: int,
    keys: Mapping[str, bool],
) -> None:
    connection.executemany(
        "INSERT INTO component_config_keys (component_id, key, is_set) VALUES (?, ?, ?)",
        [(component_id, key, int(is_set)) for key, is_set in keys.items()],
    )
