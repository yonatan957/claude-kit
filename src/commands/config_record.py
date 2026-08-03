"""Recording a manually-placed component as "user"-sourced (FR-043).

Separate from detection (`config_collision.py`) because this builds
`installed.json` entries, which is a different concern from deciding whether a
collision exists.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.core.diffing import content_hash
from src.core.state_model import (
    Component,
    ContentEntry,
    InstalledRecord,
    PluginEntry,
    ScriptConfig,
    ScriptEntry,
)


def record_user_sourced(
    category: str, name: str, component: Component, installed: InstalledRecord
) -> None:
    """FR-043's confirmed outcome: track the item without touching it — no
    file copy, no registration, just a "user"-sourced ledger entry."""
    if component.handler == "content":
        entry = ContentEntry(
            source="user", installed_hash=content_hash(component), installed_at=datetime.now(UTC)
        )
    elif component.handler == "marketplace":
        entry = PluginEntry(
            source="user",
            marketplace=component.marketplace or "",
            version=component.version,
            enabled=True,
        )
    else:
        entry = ScriptEntry(
            source="user",
            version=component.version,
            installed_hash="",
            config=ScriptConfig(status="pending"),
        )
    getattr(installed, category)[name] = entry
