"""Selection markers (FR-047).

All three glyphs are the same display width, so a row never shifts
horizontally when its state changes.
"""

from __future__ import annotations

from src.ui.entry import SelectionState

_GLYPHS: dict[SelectionState, tuple[str, str]] = {
    SelectionState.UNSELECTED: ("[ ]", ""),
    SelectionState.SELECTED: ("[✓]", "class:selected"),
    SelectionState.PENDING_REMOVAL: ("[X]", "class:removal"),
}

GLYPH_WIDTH = 3


def glyph_for(state: SelectionState) -> tuple[str, str]:
    """Return `(glyph, style_class)` for a selection state."""
    return _GLYPHS[state]
