"""Every value the kit takes from the environment, read once at import.

A variable that is unset or unreadable falls back to the default beside it, so
a bad ``CLAUDE_KIT_TIMEOUT`` slows nothing down and breaks nothing.
"""

import os
from pathlib import Path

__all__ = [
    "DEFAULT_CLAUDE_KIT_HOME",
    "CLAUDE_KIT_HOME",
    "CLAUDE_GLOBAL_MD",
    "DATABASE_FILE_NAME",
    "STATE_FILE_NAME",
    "TIMEOUT",
    "CHECK_INTERVAL_HOURS",
    "CLAUDE_BINARY",
    "CLAUDE_LABEL",
    "CLAUDE_INSTALL_COMMAND",
    "SKILLHUB_LABEL",
    "RECOMMEND_SKILL_NAME",
    "GENIE_REPO_URL",
    "GENIE_DIR_NAME",
    "GENIE_MANIFEST_FILE_NAME",
    "GENIE_MD_FILE_NAME",
    "GENIE_LABEL",
    "MCP_SCOPE",
]


def _number(value: str | None, fallback: float) -> float:
    try:
        return float(value) if value else fallback
    except ValueError:
        return fallback


DEFAULT_CLAUDE_KIT_HOME = Path.home() / ".claude-kit"
CLAUDE_KIT_HOME = Path(
    os.environ.get("CLAUDE_KIT_HOME") or DEFAULT_CLAUDE_KIT_HOME
).expanduser()
# mission 7 (CLAUDE_CONFIG_DIR) makes this configurable
CLAUDE_GLOBAL_MD = Path.home() / ".claude" / "CLAUDE.md"

DATABASE_FILE_NAME = "installed.db"
STATE_FILE_NAME = "state.json"

TIMEOUT = _number(os.environ.get("CLAUDE_KIT_TIMEOUT"), 300.0)
CHECK_INTERVAL_HOURS = int(
    _number(os.environ.get("CLAUDE_KIT_CHECK_INTERVAL_HOURS"), 24)
)

CLAUDE_BINARY = os.environ.get("CLAUDE_BIN") or "claude"
CLAUDE_LABEL = "Claude Code"
CLAUDE_INSTALL_COMMAND = ("npm", "install", "-g", "@anthropic-ai/claude-code")
SKILLHUB_LABEL = "SkillHub CLI"

# TODO: the published name of the skill `ck recommend` installs and opens Claude with.
RECOMMEND_SKILL_NAME = "skill-hub-manager"

# TODO: our GitLab repo, e.g. https://gitlab.internal/<group>/genie.git
DEFAULT_GENIE_REPO_URL = "https://gitlab.com/yonatan22660/genie.git"
GENIE_REPO_URL = os.environ.get("GENIE_REPO_URL") or DEFAULT_GENIE_REPO_URL
GENIE_DIR_NAME = "genie"
GENIE_MANIFEST_FILE_NAME = "manifest.json"
GENIE_MD_FILE_NAME = "genie.md"
GENIE_LABEL = "genie"
MCP_SCOPE = "user"
