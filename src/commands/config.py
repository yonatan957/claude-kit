"""`claude-kit config [<type>]` — typer entrypoint.

Routing only: this module wires user input to `src/ui/tui.py`'s screens, which in
turn call `src/core/*` for all diffing/mutation. It never implements picker logic
itself (Constitution II — Core Has No Voice keeps that in core/, not here either).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from src.registry.catalog import CatalogError, component_type_names, load_installed, load_registry
from src.ui import tui

app = typer.Typer(help="claude-kit config — the picker/configure flow")

DEFAULT_REGISTRY_PATH = Path.home() / ".claude-kit-repo" / "registry.json"
DEFAULT_INSTALLED_PATH = Path.home() / ".claude-kit" / "installed.json"


@app.command()
def config(
    component_type: str = typer.Argument(
        None, help="Optional: one type declared by the registry (e.g. skills, agents, plugins, tools, mcps)"
    ),
    recommended: bool = typer.Option(False, "--recommended", help="Re-align with the blessed set"),
    registry_path: Path = typer.Option(DEFAULT_REGISTRY_PATH, hidden=True),
    installed_path: Path = typer.Option(DEFAULT_INSTALLED_PATH, hidden=True),
) -> None:
    registry = load_registry(registry_path)
    installed = load_installed(installed_path)

    if component_type is not None:
        valid_types = component_type_names(registry)
        if component_type not in valid_types:
            typer.secho(
                f"Unknown component type '{component_type}'. Known types: {', '.join(sorted(valid_types))}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    tui.run_config_flow(
        registry=registry,
        installed=installed,
        installed_path=installed_path,
        component_type=component_type,
        force_recommended=recommended,
    )


if __name__ == "__main__":
    app()
