"""One row's data and its derived selection state (FR-047).

Deliberately free of any `prompt_toolkit` import: this is the bottom of the
`ui/` layering chain, so everything above it — widgets, screens, the state
machine — stays testable without a terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.core.state_model import CategoryName, Component


class SelectionState(Enum):
    """The only input to a row's checkbox glyph (data-model.md)."""

    UNSELECTED = "unselected"
    SELECTED = "selected"
    PENDING_REMOVAL = "pending_removal"


@dataclass
class PickerEntry:
    category: CategoryName
    name: str
    component: Component
    currently_installed: bool
    selected: bool
    pinned: bool = False
    naming_collision: bool = False  # FR-043: a manually-placed item shares this name

    @property
    def pending_removal(self) -> bool:
        return self.currently_installed and not self.selected

    @property
    def pending_addition(self) -> bool:
        return not self.currently_installed and self.selected


def selection_state(entry: PickerEntry) -> SelectionState:
    """Derived purely from selection, never from cursor position — which is
    what keeps the marker stable as the highlight moves (FR-047)."""
    if entry.pending_removal:
        return SelectionState.PENDING_REMOVAL
    if entry.selected:
        return SelectionState.SELECTED
    return SelectionState.UNSELECTED
