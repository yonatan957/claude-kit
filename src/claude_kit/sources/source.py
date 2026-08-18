"""What every source has to be able to do."""

from abc import ABC, abstractmethod

from claude_kit.components import ClaudeComponent, ComponentKind

__all__ = ["Source"]


class Source(ABC):
    """One place components can be searched, installed and removed.

    Every method takes the kind first, because a source may serve some kinds
    and not others. A source that does not serve a kind answers with an empty
    list rather than failing -- searching every source at once must not break
    on the ones that have nothing to say.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """How this source is reported to the user, e.g. ``"skillhub"``."""

    @abstractmethod
    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        """Components of ``kind`` matching ``query``. Empty ``query`` lists all."""

    @abstractmethod
    def install(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        """Install ``name``, and answer with what was installed."""

    @abstractmethod
    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        """Remove ``name``, and answer with what was removed."""
