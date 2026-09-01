"""Names for the values that are more than a primitive or a list of them.

These carry the CLI's own vocabulary into the signatures: a scope is one of two
words, an agent is one of the profiles the CLI knows a skills directory for,
and the agent may repeat. Most of these name what goes out on a flag;
:data:`TargetAction` is the exception, naming what comes back. None of it is
checked at runtime -- the CLI stays the authority, and a profile it learns
before this list does still reaches it.
"""

import os
from collections.abc import Sequence
from typing import Literal, TypeAlias

__all__ = ["Scope", "Agent", "AgentSpec", "Directory", "TargetAction"]

#: ``--scope``: which of an agent's two skills directories to install into.
Scope: TypeAlias = Literal["user", "project"]

#: The profiles ``--agent`` accepts: the rows of the CLI's install-paths table,
#: the ones it knows a skills directory for. ``custom`` and ``generic`` are left
#: out on purpose -- the CLI writes those into a result's ``agent`` when
#: ``--dir`` or an interactive pick chose the path, but neither is a value the
#: flag takes. Hence :class:`~.Target`'s ``agent`` stays a plain ``str``: what
#: comes back is a wider set than what goes out.
Agent: TypeAlias = Literal[
    "claude-code",
    "codex",
    "cursor",
    "github-copilot",
    "gemini-cli",
    "windsurf",
    "kiro-cli",
    "roo",
    "trae",
    "trae-cn",
    "openhands",
    "openclaw",
    "opencode",
    "kilo",
]

#: ``--agent``: one profile (``"claude-code"``) or several, since the flag may
#: repeat.
AgentSpec: TypeAlias = Agent | Sequence[Agent]

#: ``--dir``: a custom install path, as a string or anything ``os.PathLike``.
Directory: TypeAlias = str | os.PathLike[str]

#: What a command did to a target, and the key its list arrives under in the
#: CLI's answer. The only word here that is an output rather than a flag, and
#: the reason a result's field name and its payload key differ.
TargetAction: TypeAlias = Literal["installed", "removed"]
