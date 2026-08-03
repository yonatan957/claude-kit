"""Catalog sync via system `git` (research.md #5): clone/pull the Catalog Repo
into ~/.claude-kit-repo. Performs real filesystem/subprocess I/O — installers/
modules may do I/O, they just never print, prompt, or exit (Principle I).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.core.paths import claude_kit_repo_dir


class CatalogSyncError(Exception):
    """Raised on a hard sync failure: no prior local cache and the remote is
    unreachable, or `git` itself is unusable."""


@dataclass
class SyncResult:
    commit: str
    synced: bool  # False when a stale local cache was used because pull failed


def _run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CatalogSyncError("system `git` binary not found on PATH") from exc


def current_commit(repo_dir: Path | None = None) -> str:
    target = repo_dir or claude_kit_repo_dir()
    result = _run_git(["rev-parse", "HEAD"], cwd=target)
    if result.returncode != 0:
        raise CatalogSyncError(
            f"unable to resolve HEAD commit in {target}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def sync_catalog(remote_url: str, repo_dir: Path | None = None) -> SyncResult:
    """Clone the Catalog Repo if absent, otherwise pull latest.

    If a prior local clone already exists and the pull fails (e.g. the
    network is unreachable), falls back to the stale local cache rather than
    raising — per cli-commands.md, only a hard failure with *no* prior cache
    is a hard error.
    """
    target = repo_dir or claude_kit_repo_dir()

    if (target / ".git").exists():
        result = _run_git(["pull", "--ff-only"], cwd=target)
        if result.returncode != 0:
            return SyncResult(commit=current_commit(target), synced=False)
        return SyncResult(commit=current_commit(target), synced=True)

    target.parent.mkdir(parents=True, exist_ok=True)
    result = _run_git(["clone", remote_url, str(target)])
    if result.returncode != 0:
        raise CatalogSyncError(f"git clone of {remote_url} failed: {result.stderr.strip()}")
    return SyncResult(commit=current_commit(target), synced=True)
