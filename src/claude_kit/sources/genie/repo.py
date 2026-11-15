"""Keeping the genie folder a shallow clone of the team's repo. Only ``ck init`` does."""

import os
import shutil
import stat
from collections.abc import Callable
from pathlib import Path

from claude_kit.helpers import (
    GENIE_LABEL,
    GENIE_MANIFEST_FILE_NAME,
    CommandResult,
    SourceError,
    SourceUnreachable,
)
from claude_kit.sources.genie.manifest import (
    Manifest,
    load_manifest,
    parse_manifest_text,
)

__all__ = ["sync_repo"]

_NO_PROMPT = {"GIT_TERMINAL_PROMPT": "0"}


def sync_repo(
    repo_url: str, genie_dir: Path, runner: Callable[..., CommandResult]
) -> Manifest:
    """Clone, or fetch and reset, ``genie_dir``; an update with a bad manifest changes nothing."""
    if not (genie_dir / ".git").exists():
        if genie_dir.exists():
            shutil.rmtree(genie_dir, onexc=_clear_read_only_and_retry)
        genie_dir.parent.mkdir(parents=True, exist_ok=True)
        _run_git(runner, "clone", "--depth", "1", "--quiet", repo_url, str(genie_dir))
        try:
            return load_manifest(genie_dir / GENIE_MANIFEST_FILE_NAME)
        except SourceError:
            shutil.rmtree(genie_dir, onexc=_clear_read_only_and_retry)
            raise

    in_dir = ("-C", str(genie_dir))
    _run_git(runner, *in_dir, "fetch", "--depth", "1", "--quiet", repo_url, "HEAD")
    manifest_text = _run_git(
        runner, *in_dir, "show", f"FETCH_HEAD:{GENIE_MANIFEST_FILE_NAME}"
    )
    manifest = parse_manifest_text(manifest_text, repo_url, genie_dir)
    _run_git(runner, *in_dir, "reset", "--hard", "--quiet", "FETCH_HEAD")
    return manifest


def _run_git(runner: Callable[..., CommandResult], *args: str) -> str:
    """Run git without prompting and return its stdout; a failure is SourceUnreachable."""
    result = runner(["git", *args], env=_NO_PROMPT)
    if not result.ok:
        reason = (
            result.message.splitlines()[-1]
            if result.message
            else f"exit {result.returncode}"
        )
        raise SourceUnreachable(GENIE_LABEL, f"git: {reason}")
    return result.stdout


def _clear_read_only_and_retry(
    remove: Callable[[str], None], path: str, _: BaseException
) -> None:
    # git leaves its pack files read-only, and Windows will not delete those
    os.chmod(path, stat.S_IWRITE)
    remove(path)
