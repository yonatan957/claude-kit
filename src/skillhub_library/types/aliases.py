"""Names for the values that are more than a primitive or a list of them.

These carry the CLI's own vocabulary into the signatures: a scope is one of two
words, an agent is one profile or several. Nothing here is validated -- the CLI
stays the authority.
"""

import os
from collections.abc import Sequence
from typing import Any, Literal, TypeAlias

__all__ = ["Scope", "AgentSpec", "Directory", "JSONObject"]

#: ``--scope``: which of an agent's two skills directories to install into.
Scope: TypeAlias = Literal["user", "project"]

#: ``--agent``: one profile name (``"claude-code"``) or several, since the
#: flag may repeat.
AgentSpec: TypeAlias = str | Sequence[str]

#: ``--dir``: a custom install path, as a string or anything ``os.PathLike``.
Directory: TypeAlias = str | os.PathLike[str]

#: A decoded JSON object -- what every result is built from.
JSONObject: TypeAlias = dict[str, Any]
