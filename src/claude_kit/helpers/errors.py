"""What the services raise when a command cannot be answered."""

from pathlib import Path

__all__ = ["KitNotFound", "SourceError"]


class KitNotFound(Exception):
    """Raised when a command needs a home that ``ck init`` has not created yet."""

    def __init__(self, home: Path) -> None:
        super().__init__(f"no kit at {home} -- run `ck init`")
        self.home = home


class SourceError(Exception):
    """Raised when a source cannot answer: its CLI is missing, or it reported a failure."""

    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"{source}: {message}")
        self.source = source
