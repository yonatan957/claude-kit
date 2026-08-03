"""Integration test: picker Step 1 driven through real key presses.

Uses `prompt_toolkit`'s `create_pipe_input()` + `DummyOutput()` in place of the
old Textual `Pilot` harness. Note there is no longer a step that presses `Tab`
to shift focus — `Tab` is now exclusively the search toggle (FR-009).
"""

import json
from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from src.core.state_model import ContentEntry, InstalledRecord, Registry
from src.ui.state import PickerState
from src.ui.tui_app import build_application, build_entries

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"

CR = "\r"
TAB = "\t"
DOWN = "\x1b[B"
ESC = "\x1b"


@pytest.fixture
def registry() -> Registry:
    return Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))


@pytest.fixture
def empty_installed() -> InstalledRecord:
    return InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T00:00:00Z",
        catalog_commit="abc",
        registry_version="1.0.0",
        cli_version="0.1.0",
    )


def drive(state: PickerState, keys: str):
    """Feed `keys` to a real Application over a pipe; return its exit value."""
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        with create_app_session(input=pipe, output=DummyOutput()):
            return build_application(state).run()


def make_state(registry, installed, **kwargs) -> PickerState:
    return PickerState(build_entries(registry, installed, **kwargs))


def test_enter_toggles_selection_and_updates_counts(registry, empty_installed):
    state = make_state(registry, empty_installed)
    target = state.visible_entries()[0]
    category = target.category
    before = dict(state.counts())[category]

    drive(state, CR + ESC)

    assert target.selected is True
    assert dict(state.counts())[category] == before + 1


def test_tab_enters_search_filters_and_pins_on_return(registry, empty_installed):
    state = make_state(registry, empty_installed)

    drive(state, TAB + "fixture-tool" + CR + TAB + ESC)

    assert [e.name for e in state.visible_entries()][0] == "fixture-tool"
    assert state.visible_entries()[0].pinned is True
    assert state.visible_entries()[0].selected is True


def test_deselecting_an_active_component_flags_pending_removal(registry, empty_installed):
    empty_installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit", installed_hash="whatever", installed_at="2026-08-03T00:00:00Z"
    )
    state = make_state(registry, empty_installed)
    skill = next(e for e in state.entries if e.name == "fixture-skill")
    assert skill.currently_installed is True

    index = state.visible_entries().index(skill)
    drive(state, DOWN * index + CR + ESC)

    assert skill.selected is False
    assert skill.pending_removal is True


def test_escape_cancels_with_zero_changes(registry, empty_installed):
    state = make_state(registry, empty_installed)

    result = drive(state, CR + ESC)

    assert result is None  # cancel returns no selection (FR-008)


def test_approve_row_returns_the_desired_selection(registry, empty_installed):
    state = make_state(registry, empty_installed)
    entry_count = len(state.visible_entries())

    # Select the first entry, walk down to the "Approve & Install" row, press Enter.
    result = drive(state, CR + DOWN * entry_count + CR)

    assert result is not None
    selected = {name for names in result.values() for name in names}
    assert state.visible_entries()[0].name in selected
