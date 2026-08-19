from enum import Enum
from .skillhub_source import SkillHubSource
from .source import Source

__all__ = ["AVAILABLE_SOURCES", "SourceName", "source_names", "source_by_name"]

#: The sources every service iterates unless it is handed its own list.
AVAILABLE_SOURCES: list[Source] = [SkillHubSource()]


def source_names(sources: list[Source] | None = None) -> list[str]:
    """The name of every source, in the same precedence order."""
    sources = AVAILABLE_SOURCES if sources is None else sources
    return [source.name for source in sources]

SourceName = Enum("SourceEnum", source_names())

def source_by_name(name: str, sources: list[Source] | None = None) -> Source | None:
    """The source called ``name``, or ``None`` when nothing answers to it."""
    sources = AVAILABLE_SOURCES if sources is None else sources
    return next((source for source in sources if source.name == name), None)