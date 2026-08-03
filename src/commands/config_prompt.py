"""Step 2 prompt invocation and its TTY guard (FR-014/FR-015)."""

from __future__ import annotations

import sys

from src.core.state_model import Component
from src.ui.configure import collect_inputs


class NoTTYError(Exception):
    """Raised when configure prompts are needed but no TTY is available.

    Without this guard, launching the prompts against a non-interactive stdin
    (CI, a piped subprocess) hangs rather than failing cleanly — discovered via
    T064's real-subprocess quickstart walkthrough.
    """


def collect_answers(name: str, component: Component) -> dict[str, str]:
    """Runs Step 2 for one component's declared inputs."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise NoTTYError(
            f"{name} requires interactive input but no TTY is available; "
            "run this in an interactive terminal, or pre-configure it via `claude-kit config`"
        )
    return collect_inputs(name, component.inputs) or {}
