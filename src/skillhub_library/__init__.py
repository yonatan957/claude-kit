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

from skillhub_library._cli import run
from skillhub_library.client import SkillHubClient
from skillhub_library.dtos import InstallRequest, Request, SearchRequest, UninstallRequest
from skillhub_library.errors import (
    CLINotFoundError,
    CLITimeoutError,
    CommandError,
    MalformedAnswerError,
    SkillHubError,
)
from skillhub_library.types import (
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
    "MalformedAnswerError",
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
