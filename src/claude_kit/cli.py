"""``ck``: the command line over claude-kit's services."""

import io
import sys
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from claude_kit import services
from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import RECOMMEND_SKILL_NAME, ExitCode, KitError, run_claude

KINDS = ", ".join(ComponentKind)
_COMPONENT_COLUMNS = ["Kind", "Name", "Version", "Source"]
_MARK_STYLES = {"✓": "green", "!": "yellow", "✗": "red"}

_out = Console(highlight=False)
_err = Console(stderr=True, highlight=False)

app = typer.Typer(name="ck", no_args_is_help=True, add_completion=False)


Kind = Annotated[ComponentKind, typer.Argument(help=f"Which kind: {KINDS}.")]
Home = Annotated[
    Path | None,
    typer.Option(help="Kit home. Defaults to $CLAUDE_KIT_HOME, else ~/.claude-kit."),
]


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Print the claude-kit version and exit."),
    ] = False,
) -> None:
    """Discover, install and remove Claude Code add-ons."""
    if version:
        _print_version()


@app.command()
def init(
    home: Home = None,
    no_install: Annotated[
        bool,
        typer.Option(
            "--no-install",
            help="Leave Claude Code and SkillHub alone when they are missing.",
        ),
    ] = False,
) -> None:
    """Set up Claude Code, every source, and the kit's home, database and state."""
    result = services.init(home=home, install_missing=not no_install)

    report = result.claude_code
    mark = "✓"
    if not report.ok:
        mark = "✗" if result.attempted_install else "!"
    detail = f"{report.status} -- {report.path or report.error}"
    _print_status(mark, report.tool.label, detail)
    for source_report in result.sources:
        _print_status(source_report.mark, source_report.label, source_report.detail)

    created = "created" if result.created_home else "already there"
    _print_status("✓", "home", f"{result.home} ({created})")
    _print_status("✓", "database", str(result.database))
    kept = "created" if result.created_state else "kept"
    _print_status("✓", "state", f"{result.state} ({kept})")

    if not result.ok:
        raise typer.Exit(ExitCode.FAILURE)

    if not report.ok or not all(source.ok for source in result.sources):
        return
    if sys.stdin.isatty() and typer.confirm(
        "Walk through recommended skills with Claude now?"
    ):
        recommend(home)
    else:
        typer.echo("run `ck recommend` to pick skills for your specialties with Claude")


@app.command()
def recommend(home: Home = None) -> None:
    """Install or update the recommendation skill, then let Claude walk you through it."""
    installed = services.recommend(home=home)
    if not installed:
        _err.print(Text(f"no source had skill {RECOMMEND_SKILL_NAME!r}", style="red"))
        raise typer.Exit(ExitCode.NOT_FOUND)
    _print_components(installed)
    raise typer.Exit(
        run_claude(
            f"Use the {RECOMMEND_SKILL_NAME} skill. Start the conversation yourself: "
            "say what we are about to do, then ask me your first question."
        )
    )


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
    kind: Kind,
    name: Annotated[str, typer.Argument(help="What to install.")],
    home: Home = None,
) -> None:
    """Install a skill, agent, mcp, tool or plugin from the first source that has it."""
    installed = services.install(kind, name, home=home)
    if not installed:
        _err.print(Text(f"no source had {kind} {name!r}", style="red"))
        raise typer.Exit(ExitCode.NOT_FOUND)
    _print_components(installed)


@app.command()
def uninstall(
    kind: Kind,
    name: Annotated[str, typer.Argument(help="What to remove.")],
    source: Annotated[str, typer.Option(help="Only look in this source.")] = "",
    home: Home = None,
) -> None:
    """Remove an installed skill, agent, mcp, tool or plugin."""
    removed = services.uninstall(
        ClaudeComponent(kind=kind, name=name, source=source), home=home
    )
    if not removed:
        _err.print(Text(f"{kind} {name!r} was not installed", style="red"))
        raise typer.Exit(ExitCode.NOT_FOUND)
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
    installed = services.get_installed_components(kind, home)
    if not installed:
        typer.echo("nothing installed")
        return
    rows = []
    for entry in installed:
        component = entry.component
        name = component.name if entry.enabled else f"{component.name} (disabled)"
        rows.append([component.kind, name, component.version or "-", component.source])
    _print_table(_COMPONENT_COLUMNS, rows)


@app.command()
def status(home: Home = None) -> None:
    """Show the last update check the kit cached."""
    state = services.get_state(home)
    typer.echo(state.message or "no message")
    if state.checked_at:
        typer.echo(f"checked at {state.checked_at}")
    rows = []
    for name, version in state.versions.items():
        behind = str(version.behind_by or "")
        rows.append([name, version.installed or "-", version.available or "-", behind])
    if rows:
        _print_table(["Name", "Installed", "Available", "Behind"], rows)


def _print_version() -> None:
    try:
        installed = metadata.version("claude-kit")
    except metadata.PackageNotFoundError:
        installed = "not installed"
    typer.echo(f"claude-kit {installed}")
    raise typer.Exit()


def _print_components(components: list[ClaudeComponent]) -> None:
    rows = [
        [component.kind, component.name, component.version or "-", component.source]
        for component in components
    ]
    _print_table(_COMPONENT_COLUMNS, rows)


def _print_table(columns: list[str], rows: list[list[str]]) -> None:
    table = Table(*columns, box=box.ROUNDED, header_style="bold")
    for row in rows:
        table.add_row(*[Text(cell) for cell in row])
    _out.print(table)


def _print_status(mark: str, label: str, detail: str) -> None:
    line = Text.assemble((mark, _MARK_STYLES[mark]), f" {label:<13} {detail}")
    _out.print(line, soft_wrap=True)


def run() -> None:
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="replace")
    try:
        app()
    except KitError as failure:
        _err.print(Text(str(failure), style="red"))
        raise SystemExit(failure.exit_code) from None


if __name__ == "__main__":
    run()
