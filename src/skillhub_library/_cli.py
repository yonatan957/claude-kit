"""Locating and invoking the SkillHub CLI."""

import json
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any

from .consts import BINARIES, BINARY_ENV_VAR, INSTALL_HINT, REQUEST_TIMEOUT
from .errors import CLINotFoundError, CLITimeoutError, CommandError

__all__ = ["run"]


def run(args: Sequence[str], *, label: str | None = None) -> str:
    """Run the CLI with ``args`` and return its stdout, or raise.

    ``label`` is how a failure names the command it came from. Requests pass
    their own, which is the command and its subject and no flags -- joining
    ``args`` instead would put ``--token`` in every error message.
    """
    argv = [_get_binary_path(), *args]
    label = label if label is not None else " ".join(args)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=REQUEST_TIMEOUT,
            stdin=subprocess.DEVNULL,  # keep the CLI non-interactive
        )
    except subprocess.TimeoutExpired:
        raise CLITimeoutError(f"`{label}` timed out after {REQUEST_TIMEOUT}s") from None

    if proc.returncode != 0:
        raise _failure(label, proc.returncode, proc.stderr, proc.stdout)
    return proc.stdout.strip()


def _failure(label: str, code: int, stderr: str, stdout: str) -> CommandError:
    """The richest error the CLI's own output allows.

    Failure envelopes come back on stderr; preferring the message inside one is
    what surfaces the CLI's own words instead of a raw JSON blob.
    """
    for text in (stderr, stdout):
        if not _is_parsable(text):
            continue
        reported: dict[str, Any] = json.loads(text)
        if reported.get("ok") is False:
            return CommandError(
                label,
                message=reported.get("message") or "no message",
                returncode=code,
                details=reported.get("details"),
                raw=reported,
            )
        break
    return CommandError(
        label,
        message=stderr.strip() or stdout.strip() or "no output",
        returncode=code,
    )


def _is_parsable(text: str) -> bool:
    """Whether ``text`` decodes as a JSON object -- not merely as JSON."""
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(decoded, dict)


def _get_binary_path() -> str:
    """The absolute path to the CLI executable, for handing to ``subprocess``."""
    for bin in BINARIES:
        found = shutil.which(bin)
        if found:
            return found
    raise CLINotFoundError(
        f"SkillHub CLI not found (tried: {', '.join(BINARIES)}). Install it with "
        f"`{INSTALL_HINT}`, or set ${BINARY_ENV_VAR}."
    )
