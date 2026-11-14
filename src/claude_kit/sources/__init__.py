"""The sources components come from, and the interface they all satisfy."""

from claude_kit.sources.genie import GenieSource
from claude_kit.sources.index import (
    AVAILABLE_SOURCES,
    SourceName,
    find_source_by_name,
    get_source,
    get_source_names,
)
from claude_kit.sources.skillhub_source import SkillHubSource
from claude_kit.sources.source import Source

__all__ = [
    "Source",
    "GenieSource",
    "SkillHubSource",
    "AVAILABLE_SOURCES",
    "SourceName",
    "get_source_names",
    "find_source_by_name",
    "get_source",
]
