"""`claude-kit update` (contracts/cli-commands.md, FR-021-FR-025/FR-044).

Frontend: printing, exit codes (Principle I). Never reads stdin. Re-syncs the
catalog and refreshes every currently-installed component in place, reusing
stored answers so nothing is ever re-prompted; per-component work lives in
`update_refresh.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import typer

from src.commands.update_refresh import all_managed_items, refresh_one
from src.core.paths import (
    catalog_remote_url,
    claude_kit_repo_dir,
    installed_json_path,
    registry_json_path,
)
from src.core.registry import RegistryError, check_min_cli_version, parse_registry
from src.core.state_model import InstalledRecord
from src.installers.catalog_sync import CatalogSyncError, sync_catalog

_CLI_VERSION = "0.1.0"


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


def run_update() -> None:
    installed = _load_installed()

    try:
        sync_result = sync_catalog(catalog_remote_url(), repo_dir=claude_kit_repo_dir())
        registry = parse_registry(registry_json_path().read_text(encoding="utf-8"))
        check_min_cli_version(registry, _CLI_VERSION)
    except (CatalogSyncError, RegistryError) as exc:
        typer.echo(f"update halted: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    items = all_managed_items(registry, installed)

    pending: list[str] = []
    failed: list[str] = []
    for item in items:
        try:
            refresh_one(item, registry, installed, pending)
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
