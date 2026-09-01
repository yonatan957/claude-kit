"""What a command exits with when it cannot be answered.

Every failure the kit reports has a code from the table in the README, and the
code belongs to the error rather than to the place that raises it: adding a
failure mode is a class here, not another branch in ``cli.run``.
"""

from enum import IntEnum
from pathlib import Path

__all__ = [
    "ExitCode",
    "KitError",
    "UsageError",
    "NotFound",
    "KitNotFound",
    "SourceError",
    "SourceUnreachable",
    "Refused",
    "Conflict",
    "RolledBack",
]


class ExitCode(IntEnum):
    """The codes ``ck`` exits with, so a script can tell failures apart without
    reading the message."""

    OK = 0
    FAILURE = 1
    USAGE = 2
    NOT_FOUND = 3
    UNREACHABLE = 4
    REFUSED = 5
    CONFLICT = 6
    ROLLED_BACK = 7


class KitError(Exception):
    """A failure the user can act on: one line on stderr, never a traceback."""

    exit_code = ExitCode.FAILURE


class UsageError(KitError):
    """The command was addressed wrongly -- an unknown source, a malformed name."""

    exit_code = ExitCode.USAGE


class NotFound(KitError):
    """Nothing anywhere answers to what was asked for."""

    exit_code = ExitCode.NOT_FOUND


class KitNotFound(NotFound):
    """Raised when a command needs a home that ``ck init`` has not created yet."""

    def __init__(self, home: Path) -> None:
        super().__init__(f"no kit at {home} -- run `ck init`")
        self.home = home


class SourceError(KitError):
    """Raised when a source answered, and the answer was a failure."""

    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"{source}: {message}")
        self.source = source


class SourceUnreachable(SourceError):
    """Raised when a source could not be asked at all: no CLI, no network, no time."""

    exit_code = ExitCode.UNREACHABLE


class Refused(KitError):
    """Raised when the user declined a step the command cannot continue without."""

    exit_code = ExitCode.REFUSED


class Conflict(KitError):
    """Ambiguous, already installed, or a file you edited."""

    exit_code = ExitCode.CONFLICT


class RolledBack(KitError):
    """Raised when a command failed partway and undid everything it had done."""

    exit_code = ExitCode.ROLLED_BACK
