"""Every source the kit knows about, in precedence order.

Install consults them in this order and stops at the first one that has the
package, so the order here is the answer to "which source wins".
"""

from .skillhub_source import SkillHubSource
from .source import Source

__all__ = ["AVAILABLE_SOURCES", "source_by_name"]

#: The sources every service iterates unless it is handed its own list.
AVAILABLE_SOURCES: list[Source] = [SkillHubSource()]


def source_by_name(name: str, sources: list[Source] | None = None) -> Source | None:
    """The source called ``name``, or ``None`` when nothing answers to it."""
    sources = AVAILABLE_SOURCES if sources is None else sources
    return next((source for source in sources if source.name == name), None)
