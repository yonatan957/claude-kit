"""`claude-kit list` (contracts/cli-commands.md, FR-026/FR-027).

Frontend: printing, exit codes (Principle I). Read-only: combines the
already-synced local catalog cache with installed.json — `list` itself never
syncs (that's `update`'s job; a missing/corrupt cache is a hard error here).
"""

from __future__ import annotations

import typer

from src.core.diffing import content_hash
from src.core.paths import installed_json_path, registry_json_path
from src.core.registry import RegistryError, parse_registry
from src.core.state_model import CategoryName, InstalledRecord, Registry

_CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


class ListError(Exception):
    """Raised when the local catalog cache is missing/corrupt."""


def _load_installed() -> InstalledRecord | None:
    path = installed_json_path()
    if not path.exists():
        return None
    return InstalledRecord.model_validate_json(path.read_text(encoding="utf-8"))


def _load_registry() -> Registry:
    if not registry_json_path().exists():
        raise ListError("No local catalog cache found. Run `claude-kit update` first.")
    try:
        return parse_registry(registry_json_path().read_text(encoding="utf-8"))
    except RegistryError as exc:
        raise ListError(f"Local catalog cache is corrupt: {exc}") from exc


def build_rows(registry: Registry, installed: InstalledRecord | None) -> list[dict]:
    """Pure rendering-data builder (kept separate from printing so it's
    directly testable): one row per catalog component."""
    rows: list[dict] = []
    components_by_category = registry.components_by_category()
    for category in _CATEGORIES:
        for name, component in components_by_category[category].items():
            entry = getattr(installed, category).get(name) if installed else None
            if entry is None:
                rows.append(
                    {
                        "category": category,
                        "name": name,
                        "installed": False,
                        "current": None,
                        "config": "n/a",
                        "active": False,
                    }
                )
                continue

            if category in ("skills", "agents"):
                current = entry.installed_hash == content_hash(component)
                config, active = "n/a", True
            elif category == "plugins":
                current = entry.version == component.version
                config, active = "n/a", entry.enabled
            else:  # tools, mcps
                current = entry.version == component.version
                config, active = entry.config.status, entry.config.status == "done"

            rows.append(
                {
                    "category": category,
                    "name": name,
                    "installed": True,
                    "current": current,
                    "config": config,
                    "active": active,
                }
            )
    return rows


def _format_row(row: dict) -> str:
    installed_flag = "yes" if row["installed"] else "no"
    if row["current"] is None:
        current_flag = "n/a"
    else:
        current_flag = "current" if row["current"] else "outdated"
    config_flag = row["config"].upper() if row["config"] == "pending" else row["config"]
    active_flag = "yes" if row["active"] else "no"
    return (
        f"{row['category']:<10} {row['name']:<24} {installed_flag:<10} "
        f"{current_flag:<10} {config_flag:<10} {active_flag:<8}"
    )


def run_list() -> None:
    try:
        registry = _load_registry()
    except ListError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    installed = _load_installed()
    rows = build_rows(registry, installed)

    header = (
        f"{'CATEGORY':<10} {'NAME':<24} {'INSTALLED':<10} "
        f"{'CURRENT':<10} {'CONFIG':<10} {'ACTIVE':<8}"
    )
    typer.echo(header)
    typer.echo("-" * len(header))
    for row in rows:
        typer.echo(_format_row(row))
