"""`claude-kit config [type]` (contracts/cli-commands.md, FR-006-FR-016).

Orchestration only: load state → sync the catalog → run the picker → diff →
apply → save → report. The pieces live alongside: `config_state` (local state
I/O), `config_collision` + `config_record` (FR-043), `config_prompt` (Step 2),
`config_apply` (install/remove dispatch).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import typer

from src.commands.config_apply import apply_plan
from src.commands.config_collision import detect_all_collisions
from src.commands.config_state import load_installed, save_installed, sync_and_load_registry
from src.core.diffing import compute_selection_diff
from src.core.registry import RegistryError
from src.installers.catalog_sync import CatalogSyncError
from src.ui.tui_app import run_picker


def run_config(category: str | None = None) -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        typer.echo("claude-kit config requires an interactive terminal (TTY).", err=True)
        raise typer.Exit(code=1)

    installed = load_installed()
    try:
        registry = sync_and_load_registry(installed)
    except (CatalogSyncError, RegistryError) as exc:
        typer.echo(f"Failed to sync/parse the catalog: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    collisions = detect_all_collisions(registry, installed)
    desired = run_picker(
        registry, installed, category_filter=category, naming_collisions=collisions
    )

    if desired is None:
        typer.echo("Cancelled. No changes applied.")
        return

    plan = compute_selection_diff(registry, installed, desired)
    errors = apply_plan(plan, registry, installed)

    installed.last_updated = datetime.now(UTC)
    save_installed(installed)

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Applied {len(plan.to_add)} addition(s), {len(plan.to_remove)} removal(s).")
