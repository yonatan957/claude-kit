"""`claude-kit config [type]` (contracts/cli-commands.md, FR-006-FR-016).

Frontend: printing, exit codes, TTY checks, and driving the TUI (Principle
I) — all real install/remove work is delegated to installers/.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import typer

from src.core.diffing import DiffPlan, PlanItem, compute_selection_diff, content_hash
from src.core.paths import (
    agents_dir,
    catalog_remote_url,
    claude_kit_repo_dir,
    claude_settings_path,
    env_dir,
    installed_json_path,
    registry_json_path,
    skills_dir,
)
from src.core.registry import RegistryError, parse_registry
from src.core.state_model import (
    Component,
    ContentEntry,
    InstalledRecord,
    PluginEntry,
    Registry,
    ScriptConfig,
    ScriptEntry,
)
from src.installers.catalog_sync import CatalogSyncError, sync_catalog
from src.installers.content import install_content, relative_dest, remove_content
from src.installers.marketplace import install_plugin, remove_plugin
from src.installers.script import install_script_component, remove_script_component
from src.installers.settings_patch import get_mcp_servers
from src.ui.tui import ConfigureApp, PickerApp

_CONTENT_TARGET_DIRS = {"skills": skills_dir, "agents": agents_dir}


class NamingCollisionRefused(Exception):
    """Raised when a naming collision (FR-043) is not explicitly confirmed."""


class NoTTYError(Exception):
    """Raised when Step 2 configure prompts are needed but no TTY is
    available — without this, launching the real Textual ConfigureApp
    against a non-interactive stdin (e.g. CI, a piped subprocess) hangs
    rather than failing cleanly, discovered via T064's real-subprocess
    quickstart walkthrough (cli-commands.md's cross-command guarantee that
    `add` may read stdin only when collecting declared inputs — it must
    still refuse cleanly, not hang, when no TTY backs that stdin)."""


def _has_naming_collision(category: str, name: str, component: Component, installed: InstalledRecord) -> bool:
    """True if `name` already exists outside claude-kit's own tracking — a
    manually-placed ("user"-sourced) item — per FR-043. Never true for a name
    claude-kit already tracks (including a previously acknowledged "user"
    entry), since that's not a *new* collision."""
    if name in getattr(installed, category):
        return False
    if component.handler == "content":
        target_dir = _CONTENT_TARGET_DIRS[category]()
        return any((target_dir / relative_dest(f.path)).exists() for f in component.files)
    if category == "mcps" and component.mcp_config is not None:
        settings_path = claude_settings_path()
        if not settings_path.exists():
            return False
        raw = settings_path.read_text(encoding="utf-8")
        return name in get_mcp_servers(raw)
    return False


def _record_user_sourced(category: str, name: str, component: Component, installed: InstalledRecord) -> None:
    """FR-043's confirmed outcome: track the manually-placed item as
    "user"-sourced without touching it (no copy, no registration)."""
    if component.handler == "content":
        entry = ContentEntry(source="user", installed_hash=content_hash(component), installed_at=datetime.now(UTC))
    elif component.handler == "marketplace":
        entry = PluginEntry(
            source="user", marketplace=component.marketplace or "", version=component.version, enabled=True
        )
    else:
        entry = ScriptEntry(
            source="user",
            version=component.version,
            installed_hash="",
            config=ScriptConfig(status="pending"),
        )
    getattr(installed, category)[name] = entry


def _load_installed() -> InstalledRecord:
    path = installed_json_path()
    if path.exists():
        return InstalledRecord.model_validate_json(path.read_text(encoding="utf-8"))
    return InstalledRecord(
        state_version="1",
        last_updated=datetime.now(UTC),
        catalog_commit="",
        registry_version="",
        cli_version="0.1.0",
    )


def _save_installed(installed: InstalledRecord) -> None:
    installed_json_path().parent.mkdir(parents=True, exist_ok=True)
    installed_json_path().write_text(installed.model_dump_json(indent=2), encoding="utf-8")


def _sync_and_load_registry(installed: InstalledRecord) -> Registry:
    result = sync_catalog(catalog_remote_url(), repo_dir=claude_kit_repo_dir())
    registry = parse_registry(registry_json_path().read_text(encoding="utf-8"))
    installed.catalog_commit = result.commit
    installed.registry_version = registry.version
    return registry


def _collect_answers(name: str, component: Component) -> dict[str, str]:
    """Launches Step 2 (FR-014/FR-015) for one component's declared inputs."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise NoTTYError(
            f"{name} requires interactive input but no TTY is available; "
            "run this in an interactive terminal, or pre-configure it via `claude-kit config`"
        )
    answers = ConfigureApp(name, component.inputs).run()
    return answers or {}


def _apply_add(
    item: PlanItem,
    registry: Registry,
    installed: InstalledRecord,
    confirm_collision,
) -> None:
    category, name, component = item.category, item.name, item.component

    if _has_naming_collision(category, name, component, installed):
        if not confirm_collision(category, name):
            raise NamingCollisionRefused(
                f"{category}.{name}: refused — a manually-placed item with this name "
                "already exists and the collision was not confirmed"
            )
        _record_user_sourced(category, name, component, installed)
        return

    if component.handler == "content":
        target_dir = _CONTENT_TARGET_DIRS[category]()
        entry = install_content(category, name, component, claude_kit_repo_dir(), target_dir)
        getattr(installed, category)[name] = entry
    elif component.handler == "marketplace":
        entry = install_plugin(name, component, registry.plugin_marketplace)
        installed.plugins[name] = entry
    elif component.handler == "script":
        answers = _collect_answers(name, component) if component.inputs else {}
        entry = install_script_component(
            category,
            name,
            component,
            claude_kit_repo_dir(),
            answers,
            claude_settings_path(),
            env_dir(),
        )
        getattr(installed, category)[name] = entry


def _apply_remove(item: PlanItem, registry: Registry, installed: InstalledRecord) -> None:
    category, name, component = item.category, item.name, item.component

    existing_entry = getattr(installed, category).get(name)
    if existing_entry is not None and existing_entry.source == "user":
        # claude-kit never touched this item's files/registration (FR-043's
        # acknowledgment path only ever tracks it) — just stop tracking it.
        getattr(installed, category).pop(name, None)
        return

    if component.handler == "content":
        target_dir = _CONTENT_TARGET_DIRS[category]()
        remove_content(component, target_dir)
        getattr(installed, category).pop(name, None)
    elif component.handler == "marketplace":
        entry = installed.plugins.get(name)
        if entry is not None:
            remove_plugin(name, entry, registry.plugin_marketplace)
        installed.plugins.pop(name, None)
    elif component.handler == "script":
        remove_script_component(category, name, claude_kit_repo_dir(), claude_settings_path(), env_dir())
        getattr(installed, category).pop(name, None)


def _default_confirm_collision(category: str, name: str) -> bool:
    return typer.confirm(
        f"'{name}' already exists in {category} but was not installed by claude-kit "
        "(it appears to be placed manually). Track it as a manually-managed entry "
        "without overwriting it?",
        default=False,
    )


def _apply_plan(
    plan: DiffPlan,
    registry: Registry,
    installed: InstalledRecord,
    confirm_collision=_default_confirm_collision,
) -> list[str]:
    """Applies every addition/removal in one pass (FR-012). Returns a list of
    error messages for any items that failed; already-applied items are not
    rolled back (each item's own installer keeps its own state consistent)."""
    errors: list[str] = []
    for item in plan.to_remove:
        try:
            _apply_remove(item, registry, installed)
        except Exception as exc:  # noqa: BLE001 - surfaced to the developer as a plan error
            errors.append(f"{item.category}.{item.name}: remove failed: {exc}")
    for item in plan.to_add:
        try:
            _apply_add(item, registry, installed, confirm_collision)
        except Exception as exc:  # noqa: BLE001 - surfaced to the developer as a plan error
            errors.append(f"{item.category}.{item.name}: install failed: {exc}")
    return errors


def _detect_all_collisions(registry: Registry, installed: InstalledRecord) -> dict[str, set[str]]:
    """Every catalog component that would collide with a manually-placed item
    if selected — used only to visually flag entries in the picker (FR-043)."""
    collisions: dict[str, set[str]] = {}
    for category, components in registry.components_by_category().items():
        for name, component in components.items():
            if _has_naming_collision(category, name, component, installed):
                collisions.setdefault(category, set()).add(name)
    return collisions


def run_config(category: str | None = None) -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        typer.echo("claude-kit config requires an interactive terminal (TTY).", err=True)
        raise typer.Exit(code=1)

    installed = _load_installed()
    try:
        registry = _sync_and_load_registry(installed)
    except (CatalogSyncError, RegistryError) as exc:
        typer.echo(f"Failed to sync/parse the catalog: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    collisions = _detect_all_collisions(registry, installed)
    desired = PickerApp(
        registry, installed, category_filter=category, naming_collisions=collisions
    ).run()

    if desired is None:
        typer.echo("Cancelled. No changes applied.")
        return

    plan = compute_selection_diff(registry, installed, desired)
    errors = _apply_plan(plan, registry, installed)

    installed.last_updated = datetime.now(UTC)
    _save_installed(installed)

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Applied {len(plan.to_add)} addition(s), {len(plan.to_remove)} removal(s).")
