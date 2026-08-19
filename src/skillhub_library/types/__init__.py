"""Typed views over the CLI's JSON payloads, plus the aliases its flags take.

``from_payload`` never raises: unknown keys are ignored, missing keys fall back
to a default, and ``raw`` keeps the original payload so nothing is lost. The
CLI owns the shape -- adding a field to it must not break the wrapper.
"""

from skillhub_library.types.aliases import (
    AgentSpec,
    Directory,
    FlagValue,
    JSONObject,
    Payload,
    Scope,
)
from skillhub_library.types.results import InstallResult, RemoveResult
from skillhub_library.types.search import SearchResult, Skill
from skillhub_library.types.targets import Target

__all__ = [
    "Scope",
    "AgentSpec",
    "Directory",
    "JSONObject",
    "Payload",
    "FlagValue",
    "Skill",
    "SearchResult",
    "Target",
    "InstallResult",
    "RemoveResult",
]
