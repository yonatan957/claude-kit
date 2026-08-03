"""The picker's entire color vocabulary, defined once (FR-046).

Kept deliberately small: an inline tool that borrows the terminal's own
palette reads as part of the shell rather than as an application that has
taken the screen over.
"""

from __future__ import annotations

from prompt_toolkit.styles import Style

PICKER_STYLE = Style.from_dict(
    {
        "selected": "ansigreen",
        "removal": "ansired",
        "cursor": "reverse",
        "dim": "ansibrightblack",
        "collision": "ansiyellow",
        "approve": "bold",
    }
)
