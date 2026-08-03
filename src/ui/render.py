"""Build the picker's whole viewport (FR-046).

Exactly three regions are ever drawn: the counts line, a bounded list window,
and a one-line key hint. No header, no footer widget, no theme control, no
buttons.
"""

from __future__ import annotations

from src.ui.state import Mode, PickerState
from src.ui.widgets.approve_row import render_approve_row
from src.ui.widgets.row import render_row

Fragment = tuple[str, str]

KEY_HINT = "↑↓ move · Enter select · Tab search · Esc cancel"
VIEWPORT_ROWS = 12


def window_bounds(cursor: int, total: int, height: int = VIEWPORT_ROWS) -> tuple[int, int]:
    """Scroll the fixed-height window just enough to keep the cursor visible."""
    if total <= height:
        return 0, total
    start = min(max(0, cursor - height // 2), total - height)
    return start, start + height


def _header(state: PickerState) -> list[Fragment]:
    counts = " | ".join(f"{name}: {count}" for name, count in state.counts())
    if state.mode is Mode.SEARCH:
        return [("class:dim", f"search: {state.query}_\n")]
    return [("class:dim", f"{counts}\n")]


def render(state: PickerState) -> list[Fragment]:
    fragments: list[Fragment] = _header(state)
    entries = state.visible_entries()
    start, end = window_bounds(state.cursor, state.row_count())

    for index in range(start, min(end, len(entries))):
        fragments += render_row(entries[index], is_cursor=index == state.cursor)
        fragments.append(("", "\n"))

    if state.mode is Mode.BROWSE and end > len(entries):
        to_add, to_remove = state.pending()
        fragments += render_approve_row(
            is_cursor=state.on_approve_row(), to_add=to_add, to_remove=to_remove
        )
        fragments.append(("", "\n"))

    fragments.append(("class:dim", KEY_HINT))
    return fragments
