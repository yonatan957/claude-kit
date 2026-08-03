"""`claude-kit add <type> <name>` / `claude-kit remove <type> <name>`
(contracts/cli-commands.md, FR-017-FR-020/FR-043).

Frontend: printing, exit codes (Principle I). Reuses config_cmd's per-item
install/remove dispatch and naming-collision logic — the only difference from
`config` is that Step 1 (the picker) never runs; the single named component
is the entire "plan".
"""

from __future__ import annotations

from datetime import UTC, datetime

import typer

from src.commands.config_apply import apply_add as _apply_add
from src.commands.config_apply import apply_remove as _apply_remove
from src.commands.config_collision import NamingCollisionRefused
from src.commands.config_collision import default_confirm_collision as _default_confirm_collision
from src.commands.config_prompt import NoTTYError
from src.commands.config_state import load_installed as _load_installed
from src.commands.config_state import save_installed as _save_installed
from src.commands.config_state import sync_and_load_registry as _sync_and_load_registry
from src.core.diffing import PlanItem
from src.core.registry import RegistryError
from src.core.state_model import CategoryName
from src.installers.catalog_sync import CatalogSyncError

_VALID_CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


class AddRemoveError(Exception):
    """Raised for any add/remove failure that should exit non-zero (FR-020)."""


def _validate_category(category: str) -> None:
    if category not in _VALID_CATEGORIES:
        raise AddRemoveError(
            f"Unknown category '{category}'. Valid categories: {', '.join(_VALID_CATEGORIES)}"
        )


def run_add(category: str, name: str) -> None:
    installed = _load_installed()
    try:
        registry = _sync_and_load_registry(installed)
        _validate_category(category)
        component = registry.components_by_category()[category].get(name)
        if component is None:
            raise AddRemoveError(f"No component named '{name}' in category '{category}'")

        item = PlanItem(category=category, name=name, component=component)
        _apply_add(item, registry, installed, _default_confirm_collision)
    except (
        CatalogSyncError,
        RegistryError,
        AddRemoveError,
        NamingCollisionRefused,
        NoTTYError,
    ) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001 - any installer failure, surfaced per FR-020
        typer.echo(f"{category}.{name}: install failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    installed.last_updated = datetime.now(UTC)
    _save_installed(installed)
    typer.echo(f"Installed {category}.{name}")


def run_remove(category: str, name: str) -> None:
    installed = _load_installed()
    try:
        registry = _sync_and_load_registry(installed)
        _validate_category(category)

        currently_tracked = name in getattr(installed, category)
        component = registry.components_by_category()[category].get(name)

        if component is None:
            if not currently_tracked:
                raise AddRemoveError(f"No component named '{name}' in category '{category}'")
            # No longer in the catalog but still tracked: best-effort cleanup
            # of the tracking entry alone (its removal scripts/metadata are
            # gone with it from the catalog).
            getattr(installed, category).pop(name, None)
        elif not currently_tracked:
            typer.echo(f"{category}.{name} is not installed. Nothing to do.")
            return
        else:
            item = PlanItem(category=category, name=name, component=component)
            _apply_remove(item, registry, installed)
    except (CatalogSyncError, RegistryError, AddRemoveError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001 - any installer failure, surfaced per FR-020
        typer.echo(f"{category}.{name}: remove failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    installed.last_updated = datetime.now(UTC)
    _save_installed(installed)
    typer.echo(f"Removed {category}.{name}")
