"""Regression tests for the Phase 2 TUI requirements most likely to silently
regress: inline rendering (FR-045/SC-010), the removal of the legacy `a` and
`Space` shortcuts (FR-007/FR-012), and checkbox stability (FR-047).

These assert on observable behavior rather than implementation, so they keep
holding if the rendering internals are refactored.
"""

import json
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from src.core.state_model import InstalledRecord, Registry
from src.ui.entry import SelectionState, selection_state
from src.ui.render import render
from src.ui.state import PickerState
from src.ui.tui_app import build_application, build_entries
from src.ui.widgets.checkbox import glyph_for
from src.ui.widgets.row import render_row

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"

CR = "\r"
ESC = "\x1b"

ALTERNATE_SCREEN = "?1049h"
CLEAR_SCREEN = "[2J"


@pytest.fixture
def state() -> PickerState:
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    installed = InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T00:00:00Z",
        catalog_commit="abc",
        registry_version="1.0.0",
        cli_version="0.1.0",
    )
    return PickerState(build_entries(registry, installed))


def drive(state: PickerState, keys: str):
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        with create_app_session(input=pipe, output=DummyOutput()):
            return build_application(state).run()


# --- FR-045 / SC-010: inline, scrollback-preserving -------------------------


def test_application_is_not_full_screen(state):
    with create_pipe_input() as pipe:
        with create_app_session(input=pipe, output=DummyOutput()):
            app = build_application(state)
    assert app.full_screen is False
    assert app.erase_when_done is False  # final frame stays in scrollback


def test_render_emits_no_screen_clearing_sequences(state):
    text = "".join(fragment for _, fragment in render(state))
    assert ALTERNATE_SCREEN not in text
    assert CLEAR_SCREEN not in text
    assert "\x1b" not in text  # styling is carried by classes, not raw escapes


# --- FR-007 / FR-012: the legacy shortcuts are gone -------------------------


def test_letter_a_does_not_approve(state):
    result = drive(state, "a" + ESC)
    assert result is None  # 'a' must not commit the plan (FR-012)


def test_space_does_not_toggle_selection(state):
    first = state.visible_entries()[0]
    drive(state, " " + ESC)
    assert first.selected is False  # Space is inert in browse mode (FR-007)


def test_printable_keys_are_inert_in_browse_mode(state):
    drive(state, "xyz" + ESC)
    assert state.query == ""
    assert all(not e.selected for e in state.entries)


# --- FR-047: checkbox stability across focus transitions --------------------


def _glyph_text(state: PickerState, index: int, *, is_cursor: bool) -> str:
    entry = state.visible_entries()[index]
    return render_row(entry, is_cursor=is_cursor)[0][1]


def test_glyph_is_identical_with_and_without_the_cursor(state):
    assert _glyph_text(state, 0, is_cursor=False) == _glyph_text(state, 0, is_cursor=True)


def test_all_three_glyphs_share_one_display_width():
    widths = {len(glyph_for(s)[0]) for s in SelectionState}
    assert len(widths) == 1  # rows never shift horizontally when state changes


def test_glyph_survives_moving_the_cursor_onto_and_off_a_row(state):
    before = _glyph_text(state, 1, is_cursor=False)
    state.move(1)
    during = _glyph_text(state, 1, is_cursor=True)
    state.move(1)
    after = _glyph_text(state, 1, is_cursor=False)
    assert before == during == after


def test_selected_and_pending_removal_use_distinct_glyphs():
    glyphs = {s: glyph_for(s)[0] for s in SelectionState}
    assert glyphs[SelectionState.UNSELECTED] == "[ ]"
    assert glyphs[SelectionState.SELECTED] == "[✓]"
    assert glyphs[SelectionState.PENDING_REMOVAL] == "[X]"
    assert len(set(glyphs.values())) == 3


def test_deselecting_an_installed_entry_switches_glyph_to_pending_removal(state):
    entry = state.entries[0]
    entry.currently_installed = True
    entry.selected = True
    assert glyph_for(selection_state(entry))[0] == "[✓]"

    entry.selected = False
    assert glyph_for(selection_state(entry))[0] == "[X]"


# --- Row truncation: no mid-word clipping at the terminal edge ---------------


def _row_text(state: PickerState, index: int, width: int | None) -> str:
    entry = state.visible_entries()[index]
    return "".join(text for _, text in render_row(entry, is_cursor=False, width=width))


def test_long_row_is_truncated_with_an_ellipsis(state):
    """Regression: rows used to be hard-clipped mid-word by the terminal edge,
    so a description ended like "for automat" and read as a crash."""
    text = _row_text(state, 0, width=48)

    assert len(text) <= 48
    assert text.endswith("…")


def test_truncation_never_eats_the_marker_or_name(state):
    entry = state.visible_entries()[0]
    text = _row_text(state, 0, width=40)

    assert text.startswith("[")  # marker survives
    assert entry.name in text  # identity survives


def test_no_truncation_when_the_row_already_fits(state):
    entry = state.visible_entries()[0]
    text = _row_text(state, 0, width=200)

    assert entry.component.description in text
    assert "…" not in text


def test_very_narrow_width_drops_the_description_entirely(state):
    entry = state.visible_entries()[0]
    text = _row_text(state, 0, width=len(entry.name) + 20)

    assert entry.name in text
    assert "—" not in text  # no dangling separator with nothing after it
