"""Integration test (Textual `Pilot`): picker Step 1 — toggle selections
update live per-category counts, search mode filters and pins selections,
deselecting an active component flags it as pending removal, cancel applies
zero changes (FR-006-FR-013)."""

import json
from pathlib import Path

import pytest

from src.core.state_model import ContentEntry, InstalledRecord, Registry
from src.ui.tui import PickerApp

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"


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


async def test_toggle_updates_live_selection_and_count(registry, empty_installed):
    app = PickerApp(registry, empty_installed)
    async with app.run_test() as pilot:
        await pilot.pause()
        target_category = app.entries[0].category
        before = sum(1 for e in app.entries if e.category == target_category and e.selected)

        await pilot.press("space")
        await pilot.pause()

        assert app.entries[0].selected is True
        after = sum(1 for e in app.entries if e.category == target_category and e.selected)
        assert after == before + 1
        counts_text = app.query_one("#counts").content
        assert f"{target_category}: {after}" in str(counts_text)


async def test_search_mode_filters_and_pins_on_return(registry, empty_installed):
    app = PickerApp(registry, empty_installed)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("/")
        await pilot.pause()
        assert app.search_mode is True

        for ch in "fixture-tool":
            await pilot.press(ch)
        await pilot.pause()

        visible = app._visible_entries()
        assert {e.name for e in visible} == {"fixture-tool"}

        await pilot.press("tab")  # move focus from the search input to the list
        await pilot.press("space")  # select the only visible (filtered) result
        await pilot.pause()

        await pilot.press("escape")  # return to browsing
        await pilot.pause()

        assert app.search_mode is False
        vis = app._visible_entries()
        assert vis[0].name == "fixture-tool"
        assert vis[0].pinned is True


async def test_deselecting_active_component_flags_pending_removal(registry, empty_installed):
    empty_installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit", installed_hash="whatever", installed_at="2026-08-03T00:00:00Z"
    )
    app = PickerApp(registry, empty_installed)
    async with app.run_test() as pilot:
        await pilot.pause()
        skill_entry = next(e for e in app.entries if e.name == "fixture-skill")
        assert skill_entry.currently_installed is True
        assert skill_entry.pending_removal is False

        await pilot.press("space")  # deselect the currently-active skill
        await pilot.pause()

        assert skill_entry.selected is False
        assert skill_entry.pending_removal is True


async def test_cancel_applies_zero_changes(registry, empty_installed):
    app = PickerApp(registry, empty_installed)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space")  # make a selection
        await pilot.pause()
        await pilot.press("q")  # cancel
        await pilot.pause()

    assert app.return_value is None
    assert app.cancelled is True
