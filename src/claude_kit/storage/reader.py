"""Questions asked of ``installed.db``."""

import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from types import MappingProxyType

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.components.installed_component import (
    ComponentConfig,
    ConfigStatus,
    InstalledComponent,
)
from claude_kit.storage.schema import COMPONENT_COLUMNS, name_filter

__all__ = ["get_installed_components", "find_components_by_name"]

_SELECT = f"SELECT id, {', '.join(COMPONENT_COLUMNS)} FROM installed_components"


def get_installed_components(
    connection: sqlite3.Connection,
    kind: ComponentKind | None = None,
) -> list[InstalledComponent]:
    if kind is None:
        rows = connection.execute(f"{_SELECT} ORDER BY kind, name, tag").fetchall()
    else:
        rows = connection.execute(
            f"{_SELECT} WHERE kind = ? ORDER BY name, tag", (str(kind),)
        ).fetchall()
    return _to_components(connection, rows)


def find_components_by_name(
    connection: sqlite3.Connection,
    kind: ComponentKind,
    name: str,
    tag: str = "",
) -> list[InstalledComponent]:
    where, parameters = name_filter(kind, name, tag)
    rows = connection.execute(f"{_SELECT} {where} ORDER BY tag", parameters).fetchall()
    return _to_components(connection, rows)


def _to_components(
    connection: sqlite3.Connection,
    rows: Sequence[sqlite3.Row],
) -> list[InstalledComponent]:
    if not rows:
        return []
    keys_by_id = _find_config_keys_by_id(connection, [row["id"] for row in rows])
    return [_to_component(row, keys_by_id[row["id"]]) for row in rows]


def _find_config_keys_by_id(
    connection: sqlite3.Connection,
    ids: Sequence[int],
) -> defaultdict[int, dict[str, bool]]:
    placeholders = ", ".join("?" * len(ids))
    found: defaultdict[int, dict[str, bool]] = defaultdict(dict)
    for row in connection.execute(
        "SELECT component_id, key, is_set FROM component_config_keys"
        f" WHERE component_id IN ({placeholders})",
        list(ids),
    ):
        found[row["component_id"]][row["key"]] = bool(row["is_set"])
    return found


def _to_component(row: sqlite3.Row, keys: dict[str, bool]) -> InstalledComponent:
    return InstalledComponent(
        component=ClaudeComponent(
            kind=ComponentKind(row["kind"]),
            name=row["name"],
            source=row["source"],
            description=row["description"],
            version=row["version"],
            tag=row["tag"],
        ),
        installed_at=row["installed_at"],
        installed_hash=row["installed_hash"],
        updated_at=row["updated_at"] or "",
        marketplace=row["marketplace"] or "",
        enabled=bool(row["enabled"]),
        config=ComponentConfig(
            status=ConfigStatus(row["config_status"]),
            verified_at=row["config_verified_at"] or "",
            keys=MappingProxyType(dict(keys)),
        ),
    )
