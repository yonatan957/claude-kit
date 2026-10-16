"""The ``search`` request."""

from dataclasses import dataclass

from skillhub_library.dtos._encode import connection, option
from skillhub_library.dtos.base import Request

__all__ = ["SearchRequest"]


@dataclass(frozen=True)
class SearchRequest(Request):
    """Search published skills. An empty ``query`` lists everything."""

    query: str = ""
    limit: int | None = None

    def to_args(self, *, registry: str | None = None, token: str | None = None) -> list[str]:
        return [
            "search",
            self.query,
            *connection(registry, token),
            *option("--limit", self.limit),
        ]

    @property
    def label(self) -> str:
        return f"search {self.query}".strip()
