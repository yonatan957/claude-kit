"""Typed views over the CLI's JSON payloads, plus the aliases its flags take.

``from_payload`` takes the CLI's answer already decoded -- the client owns the
JSON, these types own its shape -- and trusts :func:`~.run` to have refused
anything that was not an answer. Unknown keys are ignored, so a field added to the
CLI's output cannot break the wrapper. A *missing* one is not forgiven the same
way: where a value is the answer's whole point -- a hit's ``slug``, a target's
``dir`` -- its absence raises :class:`~.MalformedAnswerError` here, rather than
defaulting to ``""`` and surfacing later as an empty coordinate handed back to
the CLI. Only genuinely optional values keep a default. Reading a new field, though, means naming it
here: what these types carry is what this library promises, the same way
:mod:`skillhub_library.dtos` names every flag it can ever send.
"""

from .aliases import Agent, AgentSpec, Directory, Scope, TargetAction
from .results import InstallResult, SearchResult, UninstallResult
from .skill import Skill
from .targets import Target

__all__ = [
    "Scope",
    "Agent",
    "AgentSpec",
    "Directory",
    "Skill",
    "SearchResult",
    "Target",
    "TargetAction",
    "InstallResult",
    "UninstallResult",
]
