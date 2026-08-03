"""`claude-kit check` (contracts/cli-commands.md, FR-028-FR-032).

Frontend, but deliberately silent in the common case — this command is meant
to run as a detached background process (see src/notify/hook.py). Compares
local vs. remote catalog commit and local vs. latest CLI version, counts
pending configurations, and writes one pre-rendered notice to state.json.
"""

from __future__ import annotations

from datetime import UTC, datetime

import typer

from src.core.notice import render_notice
from src.core.paths import (
    catalog_remote_url,
    claude_kit_repo_dir,
    installed_json_path,
    state_json_path,
)
from src.core.state_model import Findings, InstalledRecord, NotificationSnapshot
from src.installers.catalog_sync import CatalogSyncError, sync_catalog

_CLI_VERSION = "0.1.0"
_CHECK_INTERVAL_HOURS = 6


def _latest_cli_version() -> str:
    """No live package registry is wired up in this build (out of scope) —
    defaults to "no newer version known" until one is."""
    return _CLI_VERSION


def _load_installed() -> InstalledRecord | None:
    path = installed_json_path()
    if not path.exists():
        return None
    return InstalledRecord.model_validate_json(path.read_text(encoding="utf-8"))


def _load_previous_snapshot() -> NotificationSnapshot | None:
    path = state_json_path()
    if not path.exists():
        return None
    return NotificationSnapshot.model_validate_json(path.read_text(encoding="utf-8"))


def _count_pending(installed: InstalledRecord | None) -> int:
    if installed is None:
        return 0
    count = 0
    for category in ("tools", "mcps"):
        for entry in getattr(installed, category).values():
            if entry.config.status == "pending":
                count += 1
    return count


def run_check() -> None:
    installed = _load_installed()
    local_commit = installed.catalog_commit if installed else ""

    try:
        sync_result = sync_catalog(catalog_remote_url(), repo_dir=claude_kit_repo_dir())
        remote_commit = sync_result.commit
    except CatalogSyncError:
        remote_commit = local_commit  # degraded/offline: nothing new to report on this axis

    findings = Findings(
        local_commit=local_commit,
        remote_commit=remote_commit,
        local_cli_version=_CLI_VERSION,
        latest_cli_version=_latest_cli_version(),
        pending_config_count=_count_pending(installed),
    )

    previous = _load_previous_snapshot()
    previous_announced = previous.announced if previous else []
    message, announced = render_notice(findings, previous_announced)

    snapshot = NotificationSnapshot(
        notice_version="1",
        checked_at=datetime.now(UTC),
        check_interval_hours=_CHECK_INTERVAL_HOURS,
        message=message,
        findings=findings,
        announced=announced,
    )

    try:
        state_json_path().parent.mkdir(parents=True, exist_ok=True)
        state_json_path().write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Failed to write state.json: {exc}", err=True)
        raise typer.Exit(code=1) from exc
