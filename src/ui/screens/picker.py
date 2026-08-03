"""Browse-mode view model: ordering and per-category counts (FR-006/FR-010)."""

from __future__ import annotations

from src.core.state_model import CategoryName
from src.ui.entry import PickerEntry

CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


def ordered_entries(entries: list[PickerEntry]) -> list[PickerEntry]:
    """Items selected while searching float to the top on return (FR-010)."""
    pinned = [e for e in entries if e.pinned]
    rest = [e for e in entries if not e.pinned]
    return pinned + rest


def category_counts(
    entries: list[PickerEntry], category_filter: CategoryName | None = None
) -> list[tuple[str, int]]:
    categories = (category_filter,) if category_filter else CATEGORIES
    return [
        (category, sum(1 for e in entries if e.category == category and e.selected))
        for category in categories
    ]


def pending_totals(entries: list[PickerEntry]) -> tuple[int, int]:
    """`(additions, removals)` currently staged — shown on the approve row."""
    return (
        sum(1 for e in entries if e.pending_addition),
        sum(1 for e in entries if e.pending_removal),
    )


def desired_selection(entries: list[PickerEntry]) -> dict[str, set[str]]:
    """The approved outcome: category -> set of selected names."""
    desired: dict[str, set[str]] = {category: set() for category in CATEGORIES}
    for entry in entries:
        if entry.selected:
            desired[entry.category].add(entry.name)
    return desired
