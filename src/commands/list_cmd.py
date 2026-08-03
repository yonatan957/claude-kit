"""`claude-kit list` (contracts/cli-commands.md, FR-026/FR-027).

Shows only what is actually installed — a projection of `installed.json`, not
of the catalog. Browsing what is *available* is the picker's job.

Read-only: `list` never syncs (that's `update`'s job), and a missing/corrupt
catalog cache is a hard error here because freshness cannot be computed
without it.
"""

from __future__ import annotations

import typer

from src.commands.list_format import format_row, header_line
from src.commands.list_rows import build_rows
from src.core.paths import installed_json_path, registry_json_path
from src.core.registry import RegistryError, parse_registry
from src.core.state_model import InstalledRecord, Registry

EMPTY_MESSAGE = "No components installed. Run 'claude-kit config' to add some."

__all__ = ["EMPTY_MESSAGE", "ListError", "build_rows", "run_list"]


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


def run_list() -> None:
    try:
        registry = _load_registry()
    except ListError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    rows = build_rows(registry, _load_installed())
    if not rows:
        typer.echo(EMPTY_MESSAGE)
        return

    header = header_line()
    typer.echo(header)
    typer.echo("-" * len(header))
    for row in rows:
        typer.echo(format_row(row))
