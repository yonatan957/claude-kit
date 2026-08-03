"""Naming-collision detection (FR-043).

A "collision" is a catalog component whose name already exists on disk from
something claude-kit did not install. It is never overwritten automatically;
the developer must confirm explicitly, after which `config_record.py` tracks
it as "user"-sourced.
"""

from __future__ import annotations

import typer

from src.core.paths import agents_dir, claude_settings_path, skills_dir
from src.core.state_model import Component, InstalledRecord, Registry
from src.installers.content import relative_dest
from src.installers.settings_patch import get_mcp_servers

CONTENT_TARGET_DIRS = {"skills": skills_dir, "agents": agents_dir}


class NamingCollisionRefused(Exception):
    """Raised when a naming collision is not explicitly confirmed."""


def has_naming_collision(
    category: str, name: str, component: Component, installed: InstalledRecord
) -> bool:
    """True if `name` already exists outside claude-kit's own tracking — a
    manually-placed ("user"-sourced) item. Never true for a name claude-kit
    already tracks, since that is not a *new* collision."""
    if name in getattr(installed, category):
        return False
    if component.handler == "content":
        target_dir = CONTENT_TARGET_DIRS[category]()
        return any((target_dir / relative_dest(f.path)).exists() for f in component.files)
    if category == "mcps" and component.mcp_config is not None:
        settings_path = claude_settings_path()
        if not settings_path.exists():
            return False
        return name in get_mcp_servers(settings_path.read_text(encoding="utf-8"))
    return False


def default_confirm_collision(category: str, name: str) -> bool:
    return typer.confirm(
        f"'{name}' already exists in {category} but was not installed by claude-kit "
        "(it appears to be placed manually). Track it as a manually-managed entry "
        "without overwriting it?",
        default=False,
    )


def detect_all_collisions(registry: Registry, installed: InstalledRecord) -> dict[str, set[str]]:
    """Every catalog component that would collide if selected — used only to
    visually flag entries in the picker."""
    collisions: dict[str, set[str]] = {}
    for category, components in registry.components_by_category().items():
        for name, component in components.items():
            if has_naming_collision(category, name, component, installed):
                collisions.setdefault(category, set()).add(name)
    return collisions
