"""Refreshing one already-installed component in place (FR-023/FR-024/FR-044).

Split out of `update_cmd.py`: this module decides *what happens to a single
component*, while `update_cmd.py` owns the run as a whole. Neither ever reads
stdin — `update` must never block (Principle II).
"""

from __future__ import annotations

from src.core.diffing import PlanItem
from src.core.paths import (
    agents_dir,
    claude_kit_repo_dir,
    claude_settings_path,
    env_dir,
    skills_dir,
)
from src.core.state_model import InstalledRecord, Registry
from src.installers.content import install_content
from src.installers.marketplace import install_plugin
from src.installers.script import (
    ScriptInstallError,
    install_script_component,
    load_stored_answers,
)

_CONTENT_TARGET_DIRS = {"skills": skills_dir, "agents": agents_dir}


def all_managed_items(registry: Registry, installed: InstalledRecord) -> list[PlanItem]:
    """Every component claude-kit itself installed (never a "user"-sourced,
    manually-placed entry — FR-043), paired with its current catalog
    Component. script-lifecycle.md's idempotency contract requires install/
    config/verify to be safely re-runnable, and cli-commands.md's `update`
    contract re-runs them for *every* installed component — not only ones
    whose version/hash drifted — because a credential can go stale (FR-044)
    independent of the catalog content changing at all."""
    items: list[PlanItem] = []
    for category, components in registry.components_by_category().items():
        for name, entry in getattr(installed, category).items():
            if entry.source != "claude-kit":
                continue
            component = components.get(name)
            if component is None:
                continue  # no longer in the catalog; leave installed as-is
            items.append(PlanItem(category=category, name=name, component=component))
    return items


def refresh_one(
    item: PlanItem,
    registry: Registry,
    installed: InstalledRecord,
    pending: list[str],
) -> None:
    """Re-runs one component's install lifecycle, appending to `pending` if it
    ends up awaiting configuration. Never raises for a config-stage problem."""
    category, name, component = item.category, item.name, item.component

    if component.handler == "content":
        target_dir = _CONTENT_TARGET_DIRS[category]()
        entry = install_content(category, name, component, claude_kit_repo_dir(), target_dir)
        getattr(installed, category)[name] = entry
    elif component.handler == "marketplace":
        installed.plugins[name] = install_plugin(name, component, registry.plugin_marketplace)
    elif component.handler == "script":
        _refresh_script(item, installed, pending)


def _refresh_script(item: PlanItem, installed: InstalledRecord, pending: list[str]) -> None:
    category, name, component = item.category, item.name, item.component
    try:
        entry = install_script_component(
            category,
            name,
            component,
            claude_kit_repo_dir(),
            load_stored_answers(name, env_dir()),
            claude_settings_path(),
            env_dir(),
            is_update=True,
        )
    except ScriptInstallError:
        # FR-024: a new required input (or any other config-stage issue) never
        # blocks the run — mark pending and keep going.
        existing = getattr(installed, category).get(name)
        if existing is not None:
            existing.config.status = "pending"
            existing.config.verified_at = None
        pending.append(f"{category}.{name}")
        return

    getattr(installed, category)[name] = entry
    if entry.config.status != "done":
        pending.append(f"{category}.{name}")
