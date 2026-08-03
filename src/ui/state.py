"""The picker's interaction state machine (FR-007/FR-009/FR-012).

Deliberately imports nothing from `prompt_toolkit`, so the entire interaction
model can be exercised without a terminal — see `tests/unit/test_picker_state.py`,
which drives every rule here as plain method calls. `keys.py` is a thin adapter
that maps one keypress to one method on this class and does nothing else.

Two modes, with `Tab` as the only edge between them in either direction. The
visible row list is always derived, never stored, so pinning and filtering
cannot drift out of sync with `entries`.
"""

from __future__ import annotations

from enum import Enum

from src.core.state_model import CategoryName
from src.ui.entry import PickerEntry
from src.ui.screens import picker
from src.ui.screens.search import matching_entries


class Mode(Enum):
    BROWSE = "browse"
    SEARCH = "search"


class Activation(Enum):
    TOGGLED = "toggled"
    APPROVED = "approved"


class PickerState:
    def __init__(
        self, entries: list[PickerEntry], category_filter: CategoryName | None = None
    ) -> None:
        self.entries = entries
        self.category_filter = category_filter
        self.mode = Mode.BROWSE
        self.query = ""
        self.cursor = 0

    def visible_entries(self) -> list[PickerEntry]:
        if self.mode is Mode.SEARCH:
            return matching_entries(self.entries, self.query)
        return picker.ordered_entries(self.entries)

    def row_count(self) -> int:
        """Rows the cursor can reach.

        Browse mode appends the sentinel "Approve & Install" row after the
        entries; search mode does not, which is what makes approval
        unreachable from search (FR-012).
        """
        return len(self.visible_entries()) + (1 if self.mode is Mode.BROWSE else 0)

    def on_approve_row(self) -> bool:
        return self.mode is Mode.BROWSE and self.cursor == len(self.visible_entries())

    def current_entry(self) -> PickerEntry | None:
        visible = self.visible_entries()
        return visible[self.cursor] if self.cursor < len(visible) else None

    def move(self, delta: int) -> None:
        self.cursor = max(0, min(self.cursor + delta, max(0, self.row_count() - 1)))

    def toggle_search(self) -> None:
        """`Tab` — the only edge between modes, in either direction (FR-009)."""
        if self.mode is Mode.BROWSE:
            self.mode = Mode.SEARCH
            self.query = ""
        else:
            self.mode = Mode.BROWSE
        self.cursor = 0

    def activate(self) -> Activation:
        """`Enter` — overloaded by cursor position, never by mode (FR-007/FR-012)."""
        if self.on_approve_row():
            return Activation.APPROVED
        entry = self.current_entry()
        if entry is not None:
            entry.selected = not entry.selected
            if self.mode is Mode.SEARCH and entry.selected:
                entry.pinned = True
        return Activation.TOGGLED

    def edit_query(self, char: str | None) -> None:
        """Search-mode query editing; `char=None` deletes the last character."""
        if self.mode is not Mode.SEARCH:
            return
        self.query = self.query[:-1] if char is None else self.query + char
        self.cursor = 0

    def counts(self) -> list[tuple[str, int]]:
        return picker.category_counts(self.entries, self.category_filter)

    def pending(self) -> tuple[int, int]:
        return picker.pending_totals(self.entries)

    def desired_selection(self) -> dict[str, set[str]]:
        return picker.desired_selection(self.entries)
