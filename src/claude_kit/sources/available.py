"""The sources the kit consults, in precedence order."""

from enum import Enum

from claude_kit.helpers import UsageError
from claude_kit.sources.skillhub_source import SkillHubSource
from claude_kit.sources.source import Source

__all__ = [
    "AVAILABLE_SOURCES",
    "SourceName",
    "get_source_names",
    "find_source_by_name",
    "get_source",
]

AVAILABLE_SOURCES: list[Source] = [SkillHubSource()]


def get_source_names(sources: list[Source] | None = None) -> list[str]:
    sources = sources or AVAILABLE_SOURCES
    return [source.name for source in sources]


SourceName = Enum("SourceEnum", get_source_names())


def find_source_by_name(name: str, sources: list[Source] | None = None) -> Source | None:
    sources = sources or AVAILABLE_SOURCES
    for source in sources:
        if source.name == name:
            return source
    return None


def get_source(name: str, sources: list[Source] | None = None) -> Source:
    """The source called ``name``, or a usage error that names the ones there are."""
    source = find_source_by_name(name, sources)
    if source is None:
        known = ", ".join(get_source_names(sources)) or "none"
        raise UsageError(f"unknown source {name!r} -- known sources: {known}")
    return source
