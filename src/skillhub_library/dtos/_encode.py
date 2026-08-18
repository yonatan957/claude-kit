"""Turning one option into its argv fragment.

Three shapes, and nothing generic: every flag name is written out by the
request that owns it, so a misspelling is a missing flag at review time rather
than a bogus ``--flag`` handed to the CLI at runtime.
"""

import os

from ..types import AgentSpec, Directory

__all__ = ["option", "switch", "repeated", "path", "connection"]


def option(flag: str, value: str | int | float | None) -> list[str]:
    """``--flag value``, or nothing at all when ``value`` is ``None``."""
    return [] if value is None else [flag, str(value)]


def switch(flag: str, enabled: bool) -> list[str]:
    """``--flag`` on its own, or nothing when it is off."""
    return [flag] if enabled else []


def repeated(flag: str, values: AgentSpec | None) -> list[str]:
    """``--flag a --flag b``. One bare string is one value, not its characters."""
    if values is None:
        return []
    if isinstance(values, str):
        return [flag, values]
    return [arg for value in values for arg in (flag, str(value))]


def path(flag: str, value: Directory | None) -> list[str]:
    """``--flag path``, asking ``os.PathLike`` for its own filesystem spelling."""
    return [] if value is None else [flag, os.fspath(value)]


def connection(registry: str | None, token: str | None) -> list[str]:
    """What every command carries: ``--json``, and the registry to talk to.

    ``--json`` is never optional -- it guarantees the ``{"ok": ...}`` envelope
    and keeps the CLI non-interactive (it suppresses ``install``'s scope
    prompt).
    """
    return ["--json", *option("--registry", registry), *option("--token", token)]
