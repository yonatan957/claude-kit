"""``ck``: the command line over claude-kit's services."""

from pathlib import Path
from typing import Annotated

import typer

from claude_kit import services
from claude_kit.components import ClaudeComponent, ComponentKind, InstalledComponent
from claude_kit.helpers import KitNotFound, ToolStatus

KINDS = "skill, agent, mcp, tool or plugin"

app = typer.Typer(
    name="ck",
    help="Discover, install and remove Claude Code add-ons.",
    no_args_is_help=True,
)

Kind = Annotated[ComponentKind, typer.Argument(help=f"Which kind: {KINDS}.")]
Home = Annotated[
    Path | None,
    typer.Option(help="Kit home. Defaults to $CLAUDE_KIT_HOME, else ~/.claude-kit."),
]


@app.command()
def init(
    home: Home = None,
    no_install: Annotated[
        bool,
        typer.Option(
            "--no-install", help="Leave Claude Code alone when it is missing."
        ),
    ] = False,
) -> None:
    """Set up your claude-kit environment: Claude Code, then the home, database and state."""
    result = services.init(home=home, install_missing=not no_install)
    report = result.claude_code

    if report.status is ToolStatus.PRESENT:
        typer.echo(f"{report.tool.label}: found at {report.path}")
    elif report.status is ToolStatus.INSTALLED:
        typer.secho(
            f"{report.tool.label}: installed at {report.path}", fg=typer.colors.GREEN
        )
    else:
        typer.secho(
            f"{report.tool.label}: missing -- {report.error}",
            fg=typer.colors.RED,
            err=True,
        )

    created = "created" if result.created_home else "already there"
    typer.echo(f"home:     {result.home} ({created})")
    typer.echo(f"database: {result.database}")
    typer.echo(
        f"state:    {result.state} ({'created' if result.created_state else 'kept'})"
    )

    if not result.ok:
        raise typer.Exit(1)


@app.command()
def search(
    kind: Kind,
    query: Annotated[
        str,
        typer.Argument(
            help="Text to match. Leave it out to list every one of that kind."
        ),
    ] = "",
) -> None:
    """Search every source for skills, agents, mcps, tools or plugins."""
    _print_components(services.search(kind, query))


@app.command()
def install(
    kind: Kind, name: Annotated[str, typer.Argument(help="What to install.")]
) -> None:
    """Install a skill, agent, mcp, tool or plugin from the first source that has it."""
    installed = services.install(kind, name)
    if not installed:
        typer.secho(f"no source had {kind} {name!r}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _print_components(installed)


@app.command()
def uninstall(
    kind: Kind,
    name: Annotated[str, typer.Argument(help="What to remove.")],
    source: Annotated[str, typer.Option(help="Only look in this source.")] = "",
) -> None:
    """Remove an installed skill, agent, mcp, tool or plugin."""
    removed = services.uninstall(ClaudeComponent(kind=kind, name=name, source=source))
    if not removed:
        typer.secho(
            f"{kind} {name!r} was not installed", fg=typer.colors.YELLOW, err=True
        )
        raise typer.Exit(1)
    _print_components(removed)


@app.command("list")
def list_installed(
    kind: Annotated[
        ComponentKind | None,
        typer.Option("--kind", "-k", help=f"Show only one kind: {KINDS}."),
    ] = None,
    home: Home = None,
) -> None:
    """Show every component the kit has installed."""
    installed = _run(services.get_installed_components, kind, home)
    if not installed:
        typer.echo("nothing installed")
        return
    for entry in installed:
        _print_installed_component(entry)


@app.command()
def status(home: Home = None) -> None:
    """Show the last update check the kit cached."""
    state = _run(services.get_state, home)
    typer.echo(state.message or "no message")
    if state.checked_at:
        typer.echo(f"checked at {state.checked_at}")
    for name, version in state.versions.items():
        behind = f" ({version.behind_by} behind)" if version.behind_by else ""
        installed = version.installed or "-"
        typer.echo(f"  {name:20} {installed:12} -> {version.available or '-'}{behind}")


def _run(service, *arguments):
    """Call a service that needs an initialised home, reporting when there is none."""
    try:
        return service(*arguments)
    except KitNotFound as absent:
        typer.secho(str(absent), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from None


def _print_components(components: list[ClaudeComponent]) -> None:
    for component in components:
        version = component.version or "-"
        typer.echo(
            f"{component.kind:8} {component.name:24} {version:10} {component.source}"
        )


def _print_installed_component(installed: InstalledComponent) -> None:
    component = installed.component
    version = component.version or "-"
    disabled = "" if installed.enabled else "  (disabled)"
    typer.echo(
        f"{component.kind:8} {component.name:24} {version:10} {component.source}{disabled}"
    )


if __name__ == "__main__":
    app()
