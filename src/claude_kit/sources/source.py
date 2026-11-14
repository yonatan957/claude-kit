from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from claude_kit.components import ClaudeComponent, ComponentKind

__all__ = ["InitReport", "Source"]


@dataclass(frozen=True)
class InitReport:
    ok: bool
    message: str


class Source(ABC):
    """One place components can be searched, installed and removed.

    Every method takes the kind first, because a source may serve some kinds
    and not others. A source declares the ones it serves in ``kinds``, and a
    source that does not serve a kind answers with an empty list rather than
    failing -- searching every source at once must not break on the ones that
    have nothing to say.
    """

    kinds: frozenset[ComponentKind] = frozenset()

    @property
    @abstractmethod
    def name(self) -> str:
        """How this source is reported to the user, e.g. ``"skillhub"``."""

    def supports(self, kind: ComponentKind) -> bool:
        return kind in self.kinds

    def init(self, home: Path, install_missing: bool) -> InitReport | None:
        return None

    @abstractmethod
    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        """Components of ``kind`` matching ``query``. Empty ``query`` lists all."""

    @abstractmethod
    def install(
        self, kind: ComponentKind, name: str, force: bool = False
    ) -> list[ClaudeComponent]:
        """Install ``name``, and answer with what was installed. ``force``
        overwrites a copy already on disk instead of refusing."""

    @abstractmethod
    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        """Remove ``name``, and answer with what was removed."""
