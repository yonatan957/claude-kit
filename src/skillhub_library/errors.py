"""Exceptions raised by :mod:`skillhub_library`.

Everything subclasses :class:`SkillHubError`, so ``except SkillHubError`` keeps
catching the lot.
"""

from typing import Any

__all__ = [
    "SkillHubError",
    "CLINotFoundError",
    "CLITimeoutError",
    "CommandError",
    "MalformedAnswerError",
]


class SkillHubError(RuntimeError):
    """The CLI is missing, timed out, or reported a failure."""


class CLINotFoundError(SkillHubError):
    """No SkillHub executable on PATH."""


class CLITimeoutError(SkillHubError):
    """The CLI did not finish in time."""


class CommandError(SkillHubError):
    """The CLI exited non-zero or answered ``{"ok": false}``."""

    def __init__(
        self,
        command: str,
        *,
        message: str,
        returncode: int | None = None,
        details: dict[str, Any] | None = None,
        raw: Any = None,
    ) -> None:
        self.command = command
        self.message = message
        self.returncode = returncode
        self.details = dict(details or {})
        self.raw = raw
        hint = self.details.get("next")
        super().__init__(f"{message} ({hint})" if hint else message)


class MalformedAnswerError(SkillHubError):
    """The CLI answered, but without a field this library needs.

    Raised at the point of parsing rather than defaulted away, so a payload
    that changed shape is reported where it broke instead of surfacing later
    as an empty slug handed back to the CLI.
    """
