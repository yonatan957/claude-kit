"""Render one `PickerEntry` as styled fragments.

The cursor is expressed purely as an added style class on the whole row; the
checkbox glyph itself is never altered to indicate focus. That separation is
what FR-047's "markers stay stable during focus transitions" requires.
"""

from __future__ import annotations

from src.ui.entry import PickerEntry, selection_state
from src.ui.widgets.checkbox import glyph_for

Fragment = tuple[str, str]


def _merge(base: str, extra: str) -> str:
    """Combine style classes; `prompt_toolkit` accepts a space-separated list."""
    return " ".join(part for part in (base, extra) if part)


def render_row(entry: PickerEntry, *, is_cursor: bool) -> list[Fragment]:
    glyph, glyph_style = glyph_for(selection_state(entry))
    row = "class:cursor" if is_cursor else ""

    fragments: list[Fragment] = [
        (_merge(row, glyph_style), glyph),
        (row, " "),
    ]
    if entry.naming_collision:
        fragments.append((_merge(row, "class:collision"), "(!) "))
    fragments.append((row, f"[{entry.category}] {entry.name}"))
    if entry.component.description:
        fragments.append((_merge(row, "class:dim"), f" — {entry.component.description}"))
    return fragments
