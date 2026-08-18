"""One add-on, whichever source it came from.

A source answers in these, so the rest of the kit never has to know whether a
package arrived from SkillHub, a git registry or somewhere else.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from skillhub_library.types import JSONObject

__all__ = ["ComponentKind", "ClaudeComponent"]


class ComponentKind(StrEnum):
    """The five things Claude Code can be extended with.

    The values are the words the CLI takes: ``ck install skill code-reviewer``.
    """

    SKILL = "skill"
    AGENT = "agent"
    MCP = "mcp"
    TOOL = "tool"
    PLUGIN = "plugin"


@dataclass(frozen=True)
class ClaudeComponent:
    """One add-on -- a search hit, or one that is installed.

    ``source`` names the source it came from, and is what lets a removal go
    straight to the right one; empty means unknown, and every source is asked.
    ``version`` and ``popularity`` stay empty for sources that do not publish
    them. ``tag`` is the four characters that tell two same-named packages
    apart, and only an installed component carries one. ``raw`` keeps whatever
    the source said, so nothing is lost on the way through.
    """

    kind: ComponentKind
    name: str
    description: str = ""
    source: str = ""
    version: str = ""
    popularity: int | None = None
    tag: str = ""
    raw: JSONObject = field(default_factory=dict)
