"""A thin Python wrapper around the SkillHub CLI (``clawhub`` / ``skillhub``).

    from skillhub_library import search, install, uninstall

    for skill in search("pdf", limit=10):
        print(skill.slug, skill.latest_version)

    install("pdf-parser", agent="claude-code", scope="user")
    uninstall("pdf-parser")

Every function shells out to the CLI with ``--json``. A failure raises
:class:`SkillHubError` carrying the CLI's own message, so the CLI stays the
authority on what is and isn't valid.
"""

from ._cli import run
from .errors import CLINotFoundError, CLITimeoutError, CommandError, SkillHubError
from .skills import install, search, uninstall
from .types import InstallResult, RemoveResult, SearchResult, Skill, Target

__all__ = [
    "search",
    "install",
    "uninstall",
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
    "__version__",
]

__version__ = "0.1.0"
