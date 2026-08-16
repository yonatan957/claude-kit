"""Search the registry and manage local installations."""

from __future__ import annotations

from ._cli import flags, run
from .types import InstallResult, RemoveResult, SearchResult

__all__ = ["search", "install", "uninstall"]


def search(query="", *, limit=None, registry=None, token=None):
    """Search published skills. An empty ``query`` lists everything."""
    args = ["search", query, *flags(limit=limit, registry=registry, token=token)]
    search_result = run(args)
    return SearchResult.from_payload(search_result)


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
    args = ["install", coordinate, *flags(
        namespace=namespace,
        version=version,
        scope=scope,
        agent=agent,
        dir=directory,
        force=force,
        registry=registry,
        token=token,
    )]
    return InstallResult.from_payload(run(args))


def uninstall(
    coordinate, *, namespace=None, agent=None, all_targets=False, registry=None, token=None
):
    """Remove an installed skill (the CLI's ``remove``).

    A bare slug removes matching installations across namespaces; pass a
    namespaced coordinate or ``namespace=`` to narrow it. ``all_targets``
    removes every target without prompting.
    """
    args = ["remove", coordinate, *flags(
        namespace=namespace, agent=agent, all=all_targets, registry=registry, token=token
    )]
    return RemoveResult.from_payload(run(args))
