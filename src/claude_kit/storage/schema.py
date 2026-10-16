"""The shape of ``installed.db``: what the tables are, and how a component is addressed."""

from claude_kit.components import ComponentKind

__all__ = [
    "SCHEMA_VERSION",
    "COMPONENT_COLUMNS",
    "CREATE_INSTALLED_COMPONENTS",
    "CREATE_INSTALLED_COMPONENTS_INDEX",
    "CREATE_COMPONENT_CONFIG_KEYS",
    "SCHEMA_STATEMENTS",
    "name_filter",
]

SCHEMA_VERSION = 1

CREATE_INSTALLED_COMPONENTS = """
CREATE TABLE IF NOT EXISTS installed_components (
    id                 INTEGER PRIMARY KEY,
    kind               TEXT    NOT NULL
                       CHECK (kind IN ('skill', 'agent', 'mcp', 'tool', 'plugin')),
    name               TEXT    NOT NULL,
    tag                TEXT    NOT NULL,
    source             TEXT    NOT NULL,
    description        TEXT    NOT NULL DEFAULT '',
    version            TEXT    NOT NULL DEFAULT '',
    installed_hash     TEXT    NOT NULL DEFAULT '',
    installed_at       TEXT    NOT NULL,
    updated_at         TEXT,
    marketplace        TEXT,
    enabled            INTEGER NOT NULL DEFAULT 1,
    config_status      TEXT    NOT NULL DEFAULT 'none'
                       CHECK (config_status IN ('none', 'pending', 'done')),
    config_verified_at TEXT,
    UNIQUE (kind, name, tag)
)
"""

COMPONENT_COLUMNS = (
    "kind",
    "name",
    "tag",
    "source",
    "description",
    "version",
    "installed_hash",
    "installed_at",
    "updated_at",
    "marketplace",
    "enabled",
    "config_status",
    "config_verified_at",
)

CREATE_INSTALLED_COMPONENTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_installed_components_kind_name
    ON installed_components (kind, name)
"""

CREATE_COMPONENT_CONFIG_KEYS = """
CREATE TABLE IF NOT EXISTS component_config_keys (
    component_id INTEGER NOT NULL
                 REFERENCES installed_components(id) ON DELETE CASCADE,
    key          TEXT    NOT NULL,
    is_set       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (component_id, key)
)
"""

SCHEMA_STATEMENTS = (
    CREATE_INSTALLED_COMPONENTS,
    CREATE_INSTALLED_COMPONENTS_INDEX,
    CREATE_COMPONENT_CONFIG_KEYS,
)


def name_filter(kind: ComponentKind, name: str, tag: str = "") -> tuple[str, list[str]]:
    where = "WHERE kind = ? AND name = ?"
    parameters = [str(kind), name]
    if tag:
        where += " AND tag = ?"
        parameters.append(tag)
    return where, parameters
