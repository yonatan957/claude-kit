"""Key bindings — the complete, exhaustive set (contracts/cli-commands.md).

Nothing else is bound. In particular there is no `a` approval shortcut and no
`Space` toggle (FR-007/FR-012): both fall through to the printable-character
handler, which no-ops outside search mode.

`Tab` is free to mean "toggle search" here only because this application has a
single focusable control, so focus traversal is meaningless (FR-009).
"""

from __future__ import annotations

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from src.ui.state import Activation, Mode, PickerState


def build_key_bindings(state: PickerState) -> KeyBindings:
    keys = KeyBindings()

    @keys.add("up")
    def _up(event) -> None:
        state.move(-1)

    @keys.add("down")
    def _down(event) -> None:
        state.move(1)

    @keys.add("enter")
    def _enter(event) -> None:
        if state.activate() is Activation.APPROVED:
            event.app.exit(result=state.desired_selection())

    @keys.add("tab")
    def _tab(event) -> None:
        state.toggle_search()

    @keys.add("backspace")
    def _backspace(event) -> None:
        state.edit_query(None)

    @keys.add("escape")
    def _escape(event) -> None:
        # In search, Escape returns to browsing; in browse, it cancels (FR-008).
        if state.mode is Mode.SEARCH:
            state.toggle_search()
        else:
            event.app.exit(result=None)

    @keys.add("c-c")
    def _interrupt(event) -> None:
        event.app.exit(result=None)

    @keys.add(Keys.Any)
    def _printable(event) -> None:
        if len(event.data) == 1 and event.data.isprintable():
            state.edit_query(event.data)

    return keys
