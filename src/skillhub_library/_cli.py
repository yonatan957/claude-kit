"""Locating, invoking, and unwrapping the SkillHub CLI."""

import json
import os
import shutil
import subprocess
from collections.abc import Sequence

from skillhub_library.errors import CLINotFoundError, CLITimeoutError, CommandError
from skillhub_library.types import FlagValue, Payload

__all__ = ["run", "flags", "BINARIES", "TIMEOUT"]

#: Executable names tried in order -- add a fallback here if the CLI is ever
#: published under another name. ``$SKILLHUB_BIN`` overrides the whole list.
BINARIES: tuple[str, ...] = ("skillhub",)  # note the comma: a 1-tuple, not a str

TIMEOUT = 120.0


class _Unparsed:
    """Sentinel: the CLI answered with something that isn't JSON."""


_UNPARSED = _Unparsed()


def run(args: Sequence[str], *, timeout: float = TIMEOUT) -> Payload:
    """Run the CLI with ``args`` and return its stdout parsed as JSON.

    Output that isn't JSON is returned as a plain string. Every command answers
    with an ``{"ok": ...}`` envelope -- successes on stdout, failures on stderr
    -- and ``ok`` is checked before the exit code, which is what surfaces the
    CLI's own message instead of a raw JSON blob.
    """
    argv = [_binary(), *args]
    label = " ".join(args)
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

    payload = _json(proc.stdout)
    # Successes answer on stdout, failure envelopes on stderr.
    envelope = payload if isinstance(payload, dict) else _json(proc.stderr)

    if isinstance(envelope, dict) and envelope.get("ok") is False:
        raise CommandError(
            label,
            message=envelope.get("message") or "no message",
            returncode=proc.returncode,
            details=envelope.get("details"),
            raw=envelope,
        )
    if proc.returncode != 0:
        raise CommandError(
            label,
            message=proc.stderr.strip() or proc.stdout.strip() or "no output",
            returncode=proc.returncode,
        )
    return proc.stdout.strip() if payload is _UNPARSED else payload


def _json(text: str) -> Payload | _Unparsed:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _UNPARSED


def flags(**kwargs: FlagValue) -> list[str]:
    """Build CLI flags: ``None``/``False`` are skipped, lists repeat the flag.

    ``--json`` is always present: it guarantees the envelope and keeps the CLI
    non-interactive (it suppresses ``install``'s scope prompt).
    """
    args = ["--json"]
    for name, value in kwargs.items():
        flag = "--" + name
        if value is None or value is False:
            continue
        if value is True:
            args.append(flag)
        elif isinstance(value, (list, tuple)):
            for item in value:
                args += [flag, str(item)]
        else:
            args += [flag, str(value)]
    return args


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
