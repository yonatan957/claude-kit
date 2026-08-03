"""Reading and writing claude-kit's local state for the config flow."""

from __future__ import annotations

from datetime import UTC, datetime

from src.core.paths import (
    catalog_remote_url,
    claude_kit_repo_dir,
    installed_json_path,
    registry_json_path,
)
from src.core.registry import parse_registry
from src.core.state_model import InstalledRecord, Registry
from src.installers.catalog_sync import sync_catalog


def load_installed() -> InstalledRecord:
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


def save_installed(installed: InstalledRecord) -> None:
    installed_json_path().parent.mkdir(parents=True, exist_ok=True)
    installed_json_path().write_text(installed.model_dump_json(indent=2), encoding="utf-8")


def sync_and_load_registry(installed: InstalledRecord) -> Registry:
    result = sync_catalog(catalog_remote_url(), repo_dir=claude_kit_repo_dir())
    registry = parse_registry(registry_json_path().read_text(encoding="utf-8"))
    installed.catalog_commit = result.commit
    installed.registry_version = registry.version
    return registry
