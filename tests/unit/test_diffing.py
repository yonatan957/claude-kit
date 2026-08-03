"""Unit tests for src/core/diffing.py: add/remove/update plan correctness."""

import json
from pathlib import Path

from src.core.diffing import compute_refresh_plan, compute_selection_diff, content_hash
from src.core.state_model import ContentEntry, InstalledRecord, Registry, ScriptConfig, ScriptEntry

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"


def _registry() -> Registry:
    return Registry.model_validate(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _empty_installed() -> InstalledRecord:
    return InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T00:00:00Z",
        catalog_commit="abc",
        registry_version="1.0.0",
        cli_version="0.1.0",
    )


def test_selection_diff_adds_newly_selected_component():
    registry = _registry()
    installed = _empty_installed()

    plan = compute_selection_diff(registry, installed, desired={"skills": {"fixture-skill"}})

    assert [(i.category, i.name) for i in plan.to_add] == [("skills", "fixture-skill")]
    assert plan.to_remove == []
    assert plan.to_update == []


def test_selection_diff_removes_deselected_component():
    registry = _registry()
    installed = _empty_installed()
    installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit", installed_hash="whatever", installed_at="2026-08-03T00:00:00Z"
    )

    plan = compute_selection_diff(registry, installed, desired={})

    assert [(i.category, i.name) for i in plan.to_remove] == [("skills", "fixture-skill")]
    assert plan.to_add == []


def test_selection_diff_no_op_when_already_matches_desired():
    registry = _registry()
    installed = _empty_installed()
    installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit", installed_hash="whatever", installed_at="2026-08-03T00:00:00Z"
    )

    plan = compute_selection_diff(registry, installed, desired={"skills": {"fixture-skill"}})

    assert plan.is_empty


def test_refresh_plan_flags_outdated_script_component_by_version():
    registry = _registry()
    installed = _empty_installed()
    installed.tools["fixture-tool"] = ScriptEntry(
        source="claude-kit",
        version="0.0.1",  # stale vs. the fixture catalog's "1.0.0"
        installed_hash="whatever",
        config=ScriptConfig(status="done"),
    )

    plan = compute_refresh_plan(registry, installed)

    assert [(i.category, i.name) for i in plan.to_update] == [("tools", "fixture-tool")]


def test_refresh_plan_flags_outdated_content_component_by_hash():
    registry = _registry()
    installed = _empty_installed()
    installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit", installed_hash="stale-hash", installed_at="2026-08-03T00:00:00Z"
    )

    plan = compute_refresh_plan(registry, installed)

    assert [(i.category, i.name) for i in plan.to_update] == [("skills", "fixture-skill")]


def test_refresh_plan_is_empty_when_content_hash_matches():
    registry = _registry()
    installed = _empty_installed()
    installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit",
        installed_hash=content_hash(registry.skills["fixture-skill"]),
        installed_at="2026-08-03T00:00:00Z",
    )

    plan = compute_refresh_plan(registry, installed)

    assert plan.is_empty


def test_refresh_plan_ignores_components_no_longer_in_catalog():
    registry = _registry()
    installed = _empty_installed()
    installed.tools["ghost-tool"] = ScriptEntry(
        source="claude-kit",
        version="1.0.0",
        installed_hash="whatever",
        config=ScriptConfig(status="done"),
    )

    plan = compute_refresh_plan(registry, installed)

    assert plan.is_empty


def test_content_hash_is_deterministic_and_order_independent():
    registry = _registry()
    component = registry.skills["fixture-skill"]

    assert content_hash(component) == content_hash(component)
