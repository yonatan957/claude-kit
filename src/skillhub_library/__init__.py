"""A thin Python wrapper around the SkillHub CLI (``clawhub`` / ``skillhub``).

    from skillhub_library import SkillHubClient

    client = SkillHubClient()

    for skill in client.search("pdf", limit=10):
        print(skill.slug, skill.latest_version)

    client.install("pdf-parser", agent="claude-code", scope="user")
    client.uninstall("pdf-parser")

Every command shells out to the CLI with ``--json``. A failure raises
:class:`SkillHubError` carrying the CLI's own message, so the CLI stays the
authority on what is and isn't valid.
"""

from ._cli import run
from .client import SkillHubClient
from .errors import CLINotFoundError, CLITimeoutError, CommandError, SkillHubError
from .types import (
    AgentSpec,
    Directory,
    FlagValue,
    InstallResult,
    JSONObject,
    Payload,
    RemoveResult,
    Scope,
    SearchResult,
    Skill,
    Target,
)

__all__ = [
    "SkillHubClient",
    "run",
    "SkillHubError",
    "CLINotFoundError",
    "CLITimeoutError",
    "CommandError",
    "Skill",
    "SearchResult",
    "Target",
    "InstallResult",
    "RemoveResult",
    "Scope",
    "AgentSpec",
    "Directory",
    "JSONObject",
    "Payload",
    "FlagValue",
    "__version__",
]

__version__ = "0.1.0"
