"""Building `claude-kit list`'s rows from `installed.json` (FR-026).

Iteration is driven by the installed record, not the catalog: the catalog is
consulted only to decide whether each installed copy is still current.
"""

from __future__ import annotations

from src.core.diffing import content_hash
from src.core.state_model import CategoryName, Component, InstalledRecord, Registry

CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


def row_for(category: str, name: str, entry, component: Component | None) -> dict:
    """`current is None` means "cannot be determined" — the component is
    installed but no longer present in the catalog (an orphan)."""
    if category in ("skills", "agents"):
        current = None if component is None else entry.installed_hash == content_hash(component)
        config, active = "n/a", True
    elif category == "plugins":
        current = None if component is None else entry.version == component.version
        config, active = "n/a", entry.enabled
    else:  # tools, mcps
        current = None if component is None else entry.version == component.version
        config, active = entry.config.status, entry.config.status == "done"

    return {
        "category": category,
        "name": name,
        "version": getattr(entry, "version", "—"),
        "current": current,
        "config": config,
        "active": active,
    }


def build_rows(registry: Registry, installed: InstalledRecord | None) -> list[dict]:
    """One row per *installed* component; catalog-only components are omitted."""
    if installed is None:
        return []
    by_category = registry.components_by_category()
    return [
        row_for(category, name, entry, by_category[category].get(name))
        for category in CATEGORIES
        for name, entry in getattr(installed, category).items()
    ]
