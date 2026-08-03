"""Render one `PickerEntry` as styled fragments.

The cursor is expressed purely as an added style class on the whole row; the
checkbox glyph itself is never altered to indicate focus. That separation is
what FR-047's "markers stay stable during focus transitions" requires.

Rows never wrap, so an over-long description is truncated with an ellipsis.
The marker, category and name are never truncated — they identify the row, and
a half-rendered name is worse than no description.
"""

from __future__ import annotations

from src.ui.entry import PickerEntry, selection_state
from src.ui.widgets.checkbox import glyph_for

Fragment = tuple[str, str]

ELLIPSIS = "…"
COLLISION_PREFIX = "(!) "
MIN_DESCRIPTION = 8  # below this, show no description rather than a stub


def _merge(base: str, extra: str) -> str:
    """Combine style classes; `prompt_toolkit` accepts a space-separated list."""
    return " ".join(part for part in (base, extra) if part)


def _fit(description: str, available: int) -> str:
    """Clip `description` to `available` columns, marking that it was cut."""
    if available < MIN_DESCRIPTION:
        return ""
    if len(description) <= available:
        return description
    return description[: available - 1].rstrip() + ELLIPSIS


def render_row(entry: PickerEntry, *, is_cursor: bool, width: int | None = None) -> list[Fragment]:
    glyph, glyph_style = glyph_for(selection_state(entry))
    row = "class:cursor" if is_cursor else ""

    fragments: list[Fragment] = [
        (_merge(row, glyph_style), glyph),
        (row, " "),
    ]
    if entry.naming_collision:
        fragments.append((_merge(row, "class:collision"), COLLISION_PREFIX))
    label = f"[{entry.category}] {entry.name}"
    fragments.append((row, label))

    if not entry.component.description:
        return fragments

    separator = " — "
    used = len(glyph) + 1 + (len(COLLISION_PREFIX) if entry.naming_collision else 0) + len(label)
    available = (width - used - len(separator)) if width else len(entry.component.description)
    description = _fit(entry.component.description, available)
    if description:
        fragments.append((_merge(row, "class:dim"), f"{separator}{description}"))
    return fragments
