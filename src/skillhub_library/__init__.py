"""A thin Python wrapper around the SkillHub CLI (``clawhub`` / ``skillhub``).

    from skillhub_library import search, install, uninstall

    for skill in search("pdf", limit=10):
        print(skill)

    install("pdf-parser", agent="claude-code", scope="user")
    uninstall("pdf-parser")

Every function shells out to the CLI with ``--json`` and returns the parsed
payload. A non-zero exit raises :class:`SkillHubError` carrying the CLI's own
message, so the CLI stays the authority on what is and isn't valid.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

__all__ = ["search", "install", "uninstall", "run", "SkillHubError", "__version__"]

__version__ = "0.1.0"

#: Executable names tried in order; ``$SKILLHUB_BIN`` overrides both.
BINARIES = ("clawhub", "skillhub")

TIMEOUT = 120.0


class SkillHubError(RuntimeError):
    """The CLI is missing, timed out, or exited non-zero."""


def run(args, *, timeout=TIMEOUT):
    """Run the CLI with ``args`` and return its stdout parsed as JSON.

    Output that isn't JSON is returned as a plain string.
    """
    argv = [_binary(), *args]
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
        raise SkillHubError(f"`{' '.join(args)}` timed out after {timeout}s") from None
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "no output"
        raise SkillHubError(f"`{' '.join(args)}` failed ({proc.returncode}): {message}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout.strip()


def search(query="", *, limit=None, registry=None, token=None):
    """Search published skills. An empty ``query`` lists everything."""
    args = ["search", query]
    args += _flags(limit=limit, registry=registry, token=token)
    result = run(args)
    if isinstance(result, dict):
        # The payload wraps the hits under some key -- take the list it holds.
        return next((v for v in result.values() if isinstance(v, list)), result)
    return result


def install(
    coordinate,
    *,
    namespace=None,
    version=None,
    agent=None,
    scope=None,
    directory=None,
    force=False,
    registry=None,
    token=None,
):
    """Install a skill.

    ``coordinate`` is ``slug``, ``team/slug``, ``@team/slug`` or ``team--slug``.
    ``agent`` may be one profile name or a list of them. ``directory`` installs
    to a custom path and cannot be combined with ``scope`` or ``agent``.
    """
    args = ["install", coordinate]
    args += _flags(
        namespace=namespace,
        version=version,
        scope=scope,
        agent=agent,
        dir=directory,
        force=force,
        registry=registry,
        token=token,
    )
    return run(args)


def uninstall(
    coordinate, *, namespace=None, agent=None, all_targets=False, registry=None, token=None
):
    """Remove an installed skill (the CLI's ``remove``).

    A bare slug removes matching installations across namespaces; pass a
    namespaced coordinate or ``namespace=`` to narrow it. ``all_targets``
    removes every target without prompting.
    """
    args = ["remove", coordinate]
    args += _flags(
        namespace=namespace, agent=agent, all=all_targets, registry=registry, token=token
    )
    return run(args)


def _binary():
    """Locate the CLI executable, honouring PATHEXT so Windows shims resolve."""
    names = [os.environ["SKILLHUB_BIN"]] if os.environ.get("SKILLHUB_BIN") else BINARIES
    for name in names:
        found = name if os.path.sep in name else shutil.which(name)
        if found:
            return found
    raise SkillHubError(
        f"SkillHub CLI not found (tried: {', '.join(names)}). Install it with "
        "`npm install -g @astron-team/skillhub`, or set $SKILLHUB_BIN."
    )


def _flags(**kwargs):
    """Build CLI flags: ``None``/``False`` are skipped, lists repeat the flag."""
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
