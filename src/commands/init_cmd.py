"""`claude-kit init` (FR-001-FR-005, contracts/cli-commands.md).

Frontend: printing, exit codes (Principle I). Verifies a valid Claude Code
environment, creates local directories/baseline files idempotently, deploys
genie-claude.md, appends the CLAUDE.md reference line only if absent, then
hands off to `config` Step 1.
"""

from __future__ import annotations

import typer

from src.core.paths import claude_dir, claude_kit_dir, claude_kit_repo_dir, claude_md_path, env_dir

GENIE_CLAUDE_FILENAME = "genie-claude.md"
CLAUDE_MD_REFERENCE_LINE = "@genie-claude.md"

GENIE_CLAUDE_BASELINE_CONTENT = """# genie-claude

claude-kit's baseline guidance for working with installed Skills, Agents,
Plugins, Tools, and MCP servers.

This file is owned by claude-kit; it is redeployed on every `claude-kit
init`/`claude-kit update`, so hand edits here will be overwritten.
"""


class InitError(Exception):
    """Raised when initialization cannot proceed (FR-001)."""


def verify_claude_code_environment() -> None:
    if not claude_dir().exists():
        raise InitError(
            f"No Claude Code environment found (missing {claude_dir()}). "
            "Install and run Claude Code at least once before running `claude-kit init`."
        )


def ensure_local_directories() -> None:
    """Idempotent (FR-002): safe to call on every run."""
    claude_dir().mkdir(parents=True, exist_ok=True)
    claude_kit_dir().mkdir(parents=True, exist_ok=True)
    claude_kit_repo_dir().mkdir(parents=True, exist_ok=True)
    env_dir().mkdir(parents=True, exist_ok=True)


def deploy_genie_claude() -> None:
    """Idempotent: overwrites claude-kit's own baseline file in place —
    distinct from the developer's own CLAUDE.md (FR-003)."""
    (claude_dir() / GENIE_CLAUDE_FILENAME).write_text(GENIE_CLAUDE_BASELINE_CONTENT, encoding="utf-8")


def append_claude_md_reference() -> None:
    """FR-003/FR-004: append the reference line only if not already present;
    never rewrite the developer's own content."""
    path = claude_md_path()
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if CLAUDE_MD_REFERENCE_LINE in existing:
        return
    with path.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(f"{CLAUDE_MD_REFERENCE_LINE}\n")


def run_init() -> None:
    try:
        verify_claude_code_environment()
    except InitError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    ensure_local_directories()
    deploy_genie_claude()
    append_claude_md_reference()

    typer.echo("claude-kit initialized. Launching interactive configuration...")

    from src.commands.config_cmd import run_config

    run_config(category=None)
