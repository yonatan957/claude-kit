from enum import Enum
from claude_kit.sources.skillhub_source import SkillHubSource
from claude_kit.sources.source import Source

__all__ = ["AVAILABLE_SOURCES", "SourceName", "get_source_names", "find_source_by_name"]

AVAILABLE_SOURCES: list[Source] = [SkillHubSource()]


def get_source_names(sources: list[Source] | None = None) -> list[str]:

    sources = sources or AVAILABLE_SOURCES
    return [source.name for source in sources]

SourceName = Enum("SourceEnum", get_source_names())

def find_source_by_name(name: str, sources: list[Source] | None = None) -> Source | None:

    sources = sources or AVAILABLE_SOURCES
    return [source for source in sources if source.name == name][0] or None