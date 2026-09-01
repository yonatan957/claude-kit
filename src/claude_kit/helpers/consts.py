"""Every value the kit takes from the environment, read once at import.

A variable that is unset or unreadable falls back to the default beside it, so
a bad ``CLAUDE_KIT_TIMEOUT`` slows nothing down and breaks nothing.
"""

import os
from pathlib import Path

__all__ = [
    "CLAUDE_KIT_HOME",
    "DATABASE_FILE_NAME",
    "STATE_FILE_NAME",
    "TIMEOUT",
    "CHECK_INTERVAL_HOURS",
    "CLAUDE_BINARY",
    "CLAUDE_LABEL",
    "CLAUDE_INSTALL_COMMAND",
]


def _number(value: str | None, fallback: float) -> float:
    try:
        return float(value) if value else fallback
    except ValueError:
        return fallback


CLAUDE_KIT_HOME = Path(
    os.environ.get("CLAUDE_KIT_HOME") or Path.home() / ".claude-kit"
).expanduser()

DATABASE_FILE_NAME = "installed.db"
STATE_FILE_NAME = "state.json"

TIMEOUT = _number(os.environ.get("CLAUDE_KIT_TIMEOUT"), 300.0)
CHECK_INTERVAL_HOURS = int(
    _number(os.environ.get("CLAUDE_KIT_CHECK_INTERVAL_HOURS"), 24)
)

CLAUDE_BINARY = os.environ.get("CLAUDE_BIN") or "claude"
CLAUDE_LABEL = "Claude Code"
CLAUDE_INSTALL_COMMAND = ("npm", "install", "-g", "@anthropic-ai/claude-code")
