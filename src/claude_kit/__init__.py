"""claude-kit: one uniform way to discover, install and remove Claude Code add-ons."""

from .components import ClaudeComponent, ComponentKind
from .services import InstallService, SearchService, UninstallService
from .sources import AVAILABLE_SOURCES, SkillHubSource, Source

__all__ = [
    "ComponentKind",
    "ClaudeComponent",
    "Source",
    "SkillHubSource",
    "AVAILABLE_SOURCES",
    "SearchService",
    "InstallService",
    "UninstallService",
]
