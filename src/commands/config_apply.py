"""Applying an approved add/remove plan in one pass (FR-012).

Failures are collected rather than fatal; applied items are never rolled back,
since each installer keeps its own state consistent (script-lifecycle.md).
"""

from __future__ import annotations

from src.commands.config_collision import CONTENT_TARGET_DIRS, NamingCollisionRefused
from src.commands.config_collision import default_confirm_collision, has_naming_collision
from src.commands.config_prompt import collect_answers
from src.commands.config_record import record_user_sourced
from src.core.diffing import DiffPlan, PlanItem
from src.core.paths import claude_kit_repo_dir, claude_settings_path, env_dir
from src.core.state_model import InstalledRecord, Registry
from src.installers.content import install_content, remove_content
from src.installers.marketplace import install_plugin, remove_plugin
from src.installers.script import install_script_component, remove_script_component


def apply_add(
    item: PlanItem, registry: Registry, installed: InstalledRecord, confirm_collision
) -> None:
    category, name, component = item.category, item.name, item.component

    if has_naming_collision(category, name, component, installed):
        if not confirm_collision(category, name):
            raise NamingCollisionRefused(
                f"{category}.{name}: refused — a manually-placed item with this name exists"
            )
        record_user_sourced(category, name, component, installed)
        return

    if component.handler == "content":
        target = CONTENT_TARGET_DIRS[category]()
        entry = install_content(category, name, component, claude_kit_repo_dir(), target)
        getattr(installed, category)[name] = entry
    elif component.handler == "marketplace":
        installed.plugins[name] = install_plugin(name, component, registry.plugin_marketplace)
    elif component.handler == "script":
        answers = collect_answers(name, component) if component.inputs else {}
        getattr(installed, category)[name] = install_script_component(
            category, name, component, claude_kit_repo_dir(), answers,
            claude_settings_path(), env_dir(),
        )


def apply_remove(item: PlanItem, registry: Registry, installed: InstalledRecord) -> None:
    category, name, component = item.category, item.name, item.component

    existing = getattr(installed, category).get(name)
    if existing is not None and existing.source == "user":
        # claude-kit never touched this item's files/registration — just untrack it.
        getattr(installed, category).pop(name, None)
        return

    if component.handler == "content":
        remove_content(component, CONTENT_TARGET_DIRS[category]())
    elif component.handler == "marketplace":
        entry = installed.plugins.get(name)
        if entry is not None:
            remove_plugin(name, entry, registry.plugin_marketplace)
    elif component.handler == "script":
        remove_script_component(
            category, name, claude_kit_repo_dir(), claude_settings_path(), env_dir()
        )
    getattr(installed, category).pop(name, None)


def apply_plan(
    plan: DiffPlan,
    registry: Registry,
    installed: InstalledRecord,
    confirm_collision=default_confirm_collision,
) -> list[str]:
    # One error message per failed item; an empty list means success.
    errors: list[str] = []
    for item in plan.to_remove:
        try:
            apply_remove(item, registry, installed)
        except Exception as exc:  # noqa: BLE001 - surfaced as a plan error
            errors.append(f"{item.category}.{item.name}: remove failed: {exc}")
    for item in plan.to_add:
        try:
            apply_add(item, registry, installed, confirm_collision)
        except Exception as exc:  # noqa: BLE001 - surfaced as a plan error
            errors.append(f"{item.category}.{item.name}: install failed: {exc}")
    return errors
