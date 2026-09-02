"""claude-kit: one uniform way to discover, install and remove Claude Code add-ons."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import (
    CLAUDE_KIT_HOME,
    DATABASE_FILE_NAME,
    STATE_FILE_NAME,
    ExitCode,
    KitError,
    KitNotFound,
)
from claude_kit.services import (
    InitResult,
    get_installed_components,
    get_state,
    init,
    install,
    search,
    uninstall,
)
from claude_kit.sources import AVAILABLE_SOURCES, SkillHubSource, Source

__all__ = [
    "ComponentKind",
    "ClaudeComponent",
    "Source",
    "SkillHubSource",
    "AVAILABLE_SOURCES",
    "CLAUDE_KIT_HOME",
    "DATABASE_FILE_NAME",
    "STATE_FILE_NAME",
    "InitResult",
    "init",
    "search",
    "install",
    "uninstall",
    "ExitCode",
    "KitError",
    "KitNotFound",
    "get_installed_components",
    "get_state",
]
