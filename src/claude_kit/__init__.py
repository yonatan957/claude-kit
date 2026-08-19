"""claude-kit: one uniform way to discover, install and remove Claude Code add-ons."""

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.services import install, search, uninstall
from claude_kit.sources import AVAILABLE_SOURCES, SkillHubSource, Source

__all__ = [
    "ComponentKind",
    "ClaudeComponent",
    "Source",
    "SkillHubSource",
    "AVAILABLE_SOURCES",
    "search",
    "install",
    "uninstall",
]
