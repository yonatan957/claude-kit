"""A thin Python wrapper around the SkillHub CLI (``skillhub``).

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
from .dtos import InstallRequest, Request, SearchRequest, UninstallRequest
from .errors import CLINotFoundError, CLITimeoutError, CommandError, SkillHubError
from .types import (
    Agent,
    AgentSpec,
    Directory,
    InstallResult,
    Scope,
    SearchResult,
    Skill,
    Target,
    TargetAction,
    UninstallResult,
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
    "TargetAction",
    "InstallResult",
    "UninstallResult",
    "Scope",
    "Agent",
    "AgentSpec",
    "Directory",
    "Request",
    "SearchRequest",
    "InstallRequest",
    "UninstallRequest",
    "__version__",
]

__version__ = "0.1.0"
