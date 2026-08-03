"""Search-mode view model (FR-009).

Filtering only — the approve row is deliberately absent here, so approval is
never reachable from search.
"""

from __future__ import annotations

from src.ui.entry import PickerEntry


def matching_entries(entries: list[PickerEntry], query: str) -> list[PickerEntry]:
    normalized = query.strip().lower()
    if not normalized:
        return list(entries)
    return [
        e
        for e in entries
        if normalized in e.name.lower() or normalized in e.component.description.lower()
    ]
