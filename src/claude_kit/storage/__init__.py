"""Where claude-kit remembers what it installed."""

from claude_kit.storage.database import (
    connect,
    ensure_schema,
    get_schema_version,
)
from claude_kit.storage.reader import (
    find_components_by_name,
    get_installed_components,
)
from claude_kit.storage.schema import SCHEMA_STATEMENTS, SCHEMA_VERSION
from claude_kit.storage.writer import (
    add_component,
    remove_components,
    set_component_config,
    set_component_enabled,
)

__all__ = [
    "SCHEMA_VERSION",
    "SCHEMA_STATEMENTS",
    "connect",
    "ensure_schema",
    "get_schema_version",
    "get_installed_components",
    "find_components_by_name",
    "add_component",
    "remove_components",
    "set_component_config",
    "set_component_enabled",
]
