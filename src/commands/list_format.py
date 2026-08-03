"""Column formatting for `claude-kit list` (FR-027).

There is no INSTALLED column: every row is installed by definition now, so the
column carried no information.
"""

from __future__ import annotations

_COLUMNS = (
    ("CATEGORY", 10),
    ("NAME", 24),
    ("VERSION", 10),
    ("CURRENT", 10),
    ("CONFIG", 10),
    ("ACTIVE", 8),
)


def header_line() -> str:
    return " ".join(f"{title:<{width}}" for title, width in _COLUMNS)


def _freshness(current: bool | None) -> str:
    if current is None:
        return "unknown"  # installed, but no longer in the catalog
    return "current" if current else "outdated"


def format_row(row: dict) -> str:
    # Pending configuration is upper-cased so it stands out from "done" (FR-027).
    config = row["config"].upper() if row["config"] == "pending" else row["config"]
    values = (
        row["category"],
        row["name"],
        row["version"],
        _freshness(row["current"]),
        config,
        "yes" if row["active"] else "no",
    )
    return " ".join(f"{value:<{width}}" for value, (_, width) in zip(values, _COLUMNS, strict=True))
