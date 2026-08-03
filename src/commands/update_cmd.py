"""`claude-kit update` (contracts/cli-commands.md, FR-021-FR-025/FR-044).

Frontend: printing, exit codes (Principle I). Never reads stdin. Re-syncs the
catalog and refreshes every currently-installed component in place, reusing
stored answers (src/installers/script.py's load_stored_answers) so nothing is
ever re-prompted.
"""

from __future__ import annotations

from datetime import UTC, datetime

import typer

from src.core.diffing import PlanItem
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
from src.core.registry import RegistryError, check_min_cli_version, parse_registry
from src.core.state_model import InstalledRecord, Registry
from src.installers.catalog_sync import CatalogSyncError, sync_catalog
from src.installers.content import install_content
from src.installers.marketplace import install_plugin
from src.installers.script import ScriptInstallError, install_script_component, load_stored_answers

_CLI_VERSION = "0.1.0"
_CONTENT_TARGET_DIRS = {"skills": skills_dir, "agents": agents_dir}


def _load_installed() -> InstalledRecord:
    path = installed_json_path()
    if path.exists():
        return InstalledRecord.model_validate_json(path.read_text(encoding="utf-8"))
    return InstalledRecord(
        state_version="1",
        last_updated=datetime.now(UTC),
        catalog_commit="",
        registry_version="",
        cli_version=_CLI_VERSION,
    )


def _save_installed(installed: InstalledRecord) -> None:
    installed_json_path().parent.mkdir(parents=True, exist_ok=True)
    installed_json_path().write_text(installed.model_dump_json(indent=2), encoding="utf-8")


def _all_managed_items(registry: Registry, installed: InstalledRecord) -> list[PlanItem]:
    """Every component claude-kit itself installed (never a "user"-sourced,
    manually-placed entry — FR-043), paired with its current catalog
    Component. script-lifecycle.md's idempotency contract requires install/
    config/verify to be safely re-runnable, and cli-commands.md's `update`
    contract re-runs them for *every* installed component — not only ones
    whose version/hash drifted — because a credential can go stale (FR-044)
    independent of the catalog content changing at all."""
    items: list[PlanItem] = []
    components_by_category = registry.components_by_category()
    for category, components in components_by_category.items():
        for name, entry in getattr(installed, category).items():
            if entry.source != "claude-kit":
                continue
            component = components.get(name)
            if component is None:
                continue  # no longer in the catalog; leave installed as-is
            items.append(PlanItem(category=category, name=name, component=component))
    return items


def _refresh_one(
    item: PlanItem, registry: Registry, installed: InstalledRecord, pending: list[str], failed: list[str]
) -> None:
    category, name, component = item.category, item.name, item.component
    if component.handler == "content":
        target_dir = _CONTENT_TARGET_DIRS[category]()
        entry = install_content(category, name, component, claude_kit_repo_dir(), target_dir)
        getattr(installed, category)[name] = entry
    elif component.handler == "marketplace":
        entry = install_plugin(name, component, registry.plugin_marketplace)
        installed.plugins[name] = entry
    elif component.handler == "script":
        answers = load_stored_answers(name, env_dir())
        try:
            entry = install_script_component(
                category,
                name,
                component,
                claude_kit_repo_dir(),
                answers,
                claude_settings_path(),
                env_dir(),
                is_update=True,
            )
        except ScriptInstallError:
            # FR-024: a new required input (or any other config-stage issue)
            # never blocks the run — mark pending and keep going.
            existing = getattr(installed, category).get(name)
            if existing is not None:
                existing.config.status = "pending"
                existing.config.verified_at = None
            pending.append(f"{category}.{name}")
            return
        getattr(installed, category)[name] = entry
        if entry.config.status != "done":
            pending.append(f"{category}.{name}")


def run_update() -> None:
    installed = _load_installed()

    try:
        sync_result = sync_catalog(catalog_remote_url(), repo_dir=claude_kit_repo_dir())
        registry = parse_registry(registry_json_path().read_text(encoding="utf-8"))
        check_min_cli_version(registry, _CLI_VERSION)
    except (CatalogSyncError, RegistryError) as exc:
        typer.echo(f"update halted: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    items = _all_managed_items(registry, installed)

    pending: list[str] = []
    failed: list[str] = []
    for item in items:
        try:
            _refresh_one(item, registry, installed, pending, failed)
        except Exception as exc:  # noqa: BLE001 - reported in the summary, never blocks the run
            failed.append(f"{item.category}.{item.name}: {exc}")

    installed.catalog_commit = sync_result.commit
    installed.registry_version = registry.version
    installed.last_updated = datetime.now(UTC)
    _save_installed(installed)

    typer.echo(f"Refreshed {len(items) - len(failed)} of {len(items)} component(s).")
    if pending:
        typer.echo(f"Pending configuration: {', '.join(pending)}")
    if failed:
        typer.echo(f"Failed: {', '.join(failed)}")
