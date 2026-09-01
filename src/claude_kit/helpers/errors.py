"""What the services raise when a command cannot be answered."""

from pathlib import Path

__all__ = ["KitNotFound"]


class KitNotFound(Exception):
    """Raised when a command needs a home that ``ck init`` has not created yet."""

    def __init__(self, home: Path) -> None:
        super().__init__(f"no kit at {home} -- run `ck init`")
        self.home = home
