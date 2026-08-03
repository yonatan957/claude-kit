"""Typer CLI app wiring claude-kit's command surface (contracts/cli-commands.md).

Frontend-only: argument parsing, printing, exit codes (Principle I). Each
subcommand below is currently a stub; later tasks wire each one to its real
implementation in src/commands/.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="claude-kit",
    help="Component manager for Claude Code — Skills, Agents, Plugins, Tools, and MCP servers.",
    no_args_is_help=True,
)


@app.command()
def init() -> None:
    """First-run setup: verify environment, create local state, launch config."""
    from src.commands.init_cmd import run_init

    run_init()


@app.command()
def config(
    type: str = typer.Argument(None, help="Optional category to pre-filter the picker."),
) -> None:
    """Interactive two-step picker + configure flow."""
    from src.commands.config_cmd import run_config

    run_config(category=type)


@app.command()
def update() -> None:
    """Non-interactive sync of all installed components against the latest catalog."""
    typer.echo("update: not yet implemented")
    raise typer.Exit(code=1)


@app.command()
def add(
    type: str = typer.Argument(..., help="Component category."),
    name: str = typer.Argument(..., help="Exact component name."),
) -> None:
    """Non-interactively install a single named component."""
    typer.echo("add: not yet implemented")
    raise typer.Exit(code=1)


@app.command()
def remove(
    type: str = typer.Argument(..., help="Component category."),
    name: str = typer.Argument(..., help="Exact component name."),
) -> None:
    """Non-interactively remove a single named, installed component."""
    typer.echo("remove: not yet implemented")
    raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd() -> None:
    """Read-only view of every catalog component's install/freshness/config/active status."""
    typer.echo("list: not yet implemented")
    raise typer.Exit(code=1)


@app.command()
def check() -> None:
    """Background check: refresh state.json for the next session-start notice."""
    typer.echo("check: not yet implemented")
    raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
