"""One add-on, whichever source it came from.

A source answers in these, so the rest of the kit never has to know whether a
package arrived from SkillHub, a git registry or somewhere else.
"""

from dataclasses import dataclass
from enum import StrEnum

__all__ = ["ComponentKind", "ClaudeComponent"]


class ComponentKind(StrEnum):

    SKILL = "skill"
    AGENT = "agent"
    MCP = "mcp"
    TOOL = "tool"
    PLUGIN = "plugin"


@dataclass(frozen=True)
class ClaudeComponent:

    kind: ComponentKind
    name: str
    source: str
    description: str = ""
    version: str = ""
    popularity: int | None = None
    tag: str = ""