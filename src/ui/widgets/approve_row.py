"""The sentinel "Approve & Install" row (FR-012).

Carries no checkbox glyph — it is an action, not a selectable component — and
is the only route to approval, reachable solely by moving the cursor onto it
and pressing Enter.
"""

from __future__ import annotations

Fragment = tuple[str, str]

LABEL = "Approve & Install"


def _summary(to_add: int, to_remove: int) -> str:
    if not to_add and not to_remove:
        return "no changes"
    parts = []
    if to_add:
        parts.append(f"{to_add} to add")
    if to_remove:
        parts.append(f"{to_remove} to remove")
    return ", ".join(parts)


def render_approve_row(*, is_cursor: bool, to_add: int, to_remove: int) -> list[Fragment]:
    row = "class:cursor" if is_cursor else ""
    accent = f"{row} class:approve".strip()
    return [
        (row, "    "),
        (accent, LABEL),
        (f"{row} class:dim".strip(), f"  ({_summary(to_add, to_remove)})"),
    ]
