"""Pydantic v2 models for claude-kit's three JSON engines (data-model.md).

This module is now a facade: each engine lives in its own file, and everything
is re-exported here so the many existing `from src.core.state_model import ...`
call sites keep working unchanged.

- `models_registry`  — Registry, the remote-synced Catalog (`registry.json`)
- `models_installed` — InstalledRecord, the local lockfile (`installed.json`)
- `models_state`     — NotificationSnapshot, the async cache (`state.json`)
- `models_common`    — the literal types shared across all three

Pure data definitions only — no I/O (Principle I). Callers read/write the
underlying files and hand this module raw JSON text / dicts.
"""

from __future__ import annotations

from src.core.models_common import (
    CATEGORIES,
    CategoryName,
    ConfigStatus,
    Handler,
    Source,
)
from src.core.models_installed import (
    ContentEntry,
    InstalledRecord,
    PluginEntry,
    ScriptConfig,
    ScriptEntry,
)
from src.core.models_registry import (
    Component,
    ComponentFile,
    ComponentInput,
    PluginMarketplaceCommands,
    Registry,
    TypeDeclaration,
)
from src.core.models_state import Findings, NotificationSnapshot

# Retained for backward compatibility: this private name predates the split.
_CATEGORIES = CATEGORIES

__all__ = [
    "CATEGORIES",
    "CategoryName",
    "Component",
    "ComponentFile",
    "ComponentInput",
    "ConfigStatus",
    "ContentEntry",
    "Findings",
    "Handler",
    "InstalledRecord",
    "NotificationSnapshot",
    "PluginEntry",
    "PluginMarketplaceCommands",
    "Registry",
    "ScriptConfig",
    "ScriptEntry",
    "Source",
    "TypeDeclaration",
]
