"""What every request is: a frozen set of options that knows its own argv."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

__all__ = ["Request"]


@dataclass(frozen=True)
class Request(ABC):
    """One command's arguments, ready to hand to :func:`~.._cli.run`.

    ``registry`` and ``token`` are not fields: they belong to the client, not
    to the request, and keeping the token out of the dataclass keeps it out of
    every ``repr`` and traceback that a request appears in.
    """

    @abstractmethod
    def to_args(self, *, registry: str | None = None, token: str | None = None) -> list[str]:
        """The full argument list, minus the executable itself."""

    @property
    @abstractmethod
    def label(self) -> str:
        """How this request names itself in an error message -- never its flags."""
