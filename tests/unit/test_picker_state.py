"""Unit tests for the picker's interaction state machine (FR-007/FR-009/FR-012).

No terminal, no `prompt_toolkit`, no async harness — `PickerState` is a plain
object, which is the whole point of keeping it framework-free.
"""

from __future__ import annotations

import pytest

from src.core.state_model import Component
from src.ui.entry import PickerEntry, SelectionState, selection_state
from src.ui.state import Activation, Mode, PickerState


def make_entry(name: str, category: str = "tools", *, installed: bool = False) -> PickerEntry:
    component = Component(description=f"{name} description", handler="script", version="1.0.0")
    return PickerEntry(
        category=category,
        name=name,
        component=component,
        currently_installed=installed,
        selected=installed,
    )


@pytest.fixture
def state() -> PickerState:
    return PickerState([make_entry("alpha"), make_entry("beta"), make_entry("gamma")])


def test_browse_mode_appends_a_single_approve_row(state):
    assert state.mode is Mode.BROWSE
    assert len(state.visible_entries()) == 3
    assert state.row_count() == 4  # 3 entries + the sentinel approve row


def test_cursor_clamps_at_both_ends_without_wraparound(state):
    state.move(-1)
    assert state.cursor == 0

    state.move(100)
    assert state.cursor == state.row_count() - 1
    assert state.on_approve_row()

    state.move(1)
    assert state.cursor == state.row_count() - 1  # no wrap back to the top


def test_enter_on_an_entry_toggles_selection(state):
    assert state.activate() is Activation.TOGGLED
    assert state.entries[0].selected is True

    assert state.activate() is Activation.TOGGLED
    assert state.entries[0].selected is False


def test_enter_on_the_bottom_row_approves(state):
    state.move(3)
    assert state.on_approve_row()
    assert state.activate() is Activation.APPROVED


def test_approval_is_unreachable_from_search_mode(state):
    state.toggle_search()
    state.move(100)
    assert state.on_approve_row() is False
    assert state.activate() is Activation.TOGGLED


def test_tab_round_trip_pins_entries_selected_while_searching(state):
    state.toggle_search()
    assert state.mode is Mode.SEARCH

    for char in "gamma":
        state.edit_query(char)
    assert [e.name for e in state.visible_entries()] == ["gamma"]

    state.activate()  # select the only match
    state.toggle_search()

    assert state.mode is Mode.BROWSE
    assert state.cursor == 0
    assert state.visible_entries()[0].name == "gamma"
    assert state.entries[2].pinned is True


def test_tab_clears_the_previous_query_on_re_entry(state):
    state.toggle_search()
    state.edit_query("z")
    state.toggle_search()
    state.toggle_search()
    assert state.query == ""
    assert len(state.visible_entries()) == 3


def test_backspace_edits_the_query(state):
    state.toggle_search()
    for char in "gamma":
        state.edit_query(char)
    state.edit_query(None)
    assert state.query == "gamm"


def test_query_editing_is_ignored_in_browse_mode(state):
    state.edit_query("a")
    assert state.query == ""


def test_deselecting_an_installed_entry_marks_it_pending_removal():
    state = PickerState([make_entry("alpha", installed=True)])
    entry = state.entries[0]
    assert selection_state(entry) is SelectionState.SELECTED

    state.activate()

    assert entry.selected is False
    assert selection_state(entry) is SelectionState.PENDING_REMOVAL


def test_desired_selection_reflects_a_mixed_sequence():
    state = PickerState(
        [
            make_entry("alpha", "skills", installed=True),
            make_entry("beta", "tools"),
            make_entry("gamma", "tools"),
        ]
    )
    state.activate()  # deselect the installed skill
    state.move(1)
    state.activate()  # select beta

    desired = state.desired_selection()
    assert desired["skills"] == set()
    assert desired["tools"] == {"beta"}
    assert state.pending() == (1, 1)  # one addition, one removal
