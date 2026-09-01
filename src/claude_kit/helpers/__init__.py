"""The low-level layer: what the environment says, what is on PATH, and what the kit raises."""

from claude_kit.helpers.consts import (
    CHECK_INTERVAL_HOURS,
    CLAUDE_BINARY,
    CLAUDE_INSTALL_COMMAND,
    CLAUDE_KIT_HOME,
    CLAUDE_LABEL,
    DATABASE_FILE_NAME,
    STATE_FILE_NAME,
    TIMEOUT,
)
from claude_kit.helpers.errors import KitNotFound
from claude_kit.helpers.system import (
    CommandResult,
    Tool,
    ToolReport,
    ToolStatus,
    ensure_tool,
    find_binary,
    is_installed,
    run,
)

__all__ = [
    "KitNotFound",
    "CLAUDE_KIT_HOME",
    "DATABASE_FILE_NAME",
    "STATE_FILE_NAME",
    "TIMEOUT",
    "CHECK_INTERVAL_HOURS",
    "CLAUDE_BINARY",
    "CLAUDE_LABEL",
    "CLAUDE_INSTALL_COMMAND",
    "CommandResult",
    "Tool",
    "ToolStatus",
    "ToolReport",
    "find_binary",
    "is_installed",
    "run",
    "ensure_tool",
]
