"""Locating and invoking the SkillHub CLI."""

import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any

from .errors import CLINotFoundError, CLITimeoutError, CommandError

__all__ = ["run", "BINARIES", "TIMEOUT"]

#: Executable names tried in order -- add a fallback here if the CLI is ever
#: published under another name. ``$SKILLHUB_BIN`` overrides the whole list.
BINARIES: tuple[str, ...] = ("skillhub",)  # note the comma: a 1-tuple, not a str

TIMEOUT = 120.0


def run(args: Sequence[str], *, timeout: float = TIMEOUT, label: str | None = None) -> str:
    """Run the CLI with ``args`` and return its stdout, or raise.

    ``label`` is how a failure names the command it came from. Requests pass
    their own, which is the command and its subject and no flags -- joining
    ``args`` instead would put ``--token`` in every error message.
    """
    argv = [_binary(), *args]
    label = label if label is not None else " ".join(args)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,  # keep the CLI non-interactive
        )
    except subprocess.TimeoutExpired:
        raise CLITimeoutError(f"`{label}` timed out after {timeout}s") from None

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


def _binary() -> str:
    """Locate the CLI executable, honouring PATHEXT so Windows shims resolve."""
    names = [os.environ["SKILLHUB_BIN"]] if os.environ.get("SKILLHUB_BIN") else BINARIES
    for name in names:
        found = name if os.path.sep in name else shutil.which(name)
        if found:
            return found
    raise CLINotFoundError(
        f"SkillHub CLI not found (tried: {', '.join(names)}). Install it with "
        "`npm install -g @astron-team/skillhub`, or set $SKILLHUB_BIN."
    )
