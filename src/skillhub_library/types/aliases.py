"""Names for the values that are more than a primitive or a list of them.

These carry the CLI's own vocabulary into the signatures: a scope is one of two
words, an agent is one profile or several, a payload is whatever ``--json``
answered with. Nothing here is validated -- the CLI stays the authority.
"""

import os
from collections.abc import Sequence
from typing import Any, Literal, TypeAlias

__all__ = ["Scope", "AgentSpec", "Directory", "JSONObject", "Payload"]

#: ``--scope``: which of an agent's two skills directories to install into.
Scope: TypeAlias = Literal["user", "project"]

#: ``--agent``: one profile name (``"claude-code"``) or several, since the
#: flag may repeat.
AgentSpec: TypeAlias = str | Sequence[str]

#: ``--dir``: a custom install path, as a string or anything ``os.PathLike``.
Directory: TypeAlias = str | os.PathLike[str]

#: A decoded JSON object -- the shape every ``from_payload`` expects.
JSONObject: TypeAlias = dict[str, Any]

#: What the CLI answers with: decoded JSON, or plain text when it isn't JSON.
Payload: TypeAlias = JSONObject | list[Any] | str | int | float | bool | None
