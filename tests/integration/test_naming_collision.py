"""Integration test: selecting a component name that collides with an
existing "user"-sourced (manually placed) entry is refused without explicit,
distinct confirmation (FR-043)."""

import json
from pathlib import Path

from src.commands import config_apply, config_collision, config_plan
from src.core.diffing import compute_selection_diff
from src.core.state_model import InstalledRecord, Registry

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()

_EMPTY_SELECTION = {
    "skills": set(),
    "agents": set(),
    "plugins": set(),
    "tools": set(),
    "mcps": set(),
}


def _registry() -> Registry:
    return Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))


def _empty_installed() -> InstalledRecord:
    return InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T00:00:00Z",
        catalog_commit="abc",
        registry_version="1.0.0",
        cli_version="0.1.0",
    )


def _patch_dirs(tmp_path, monkeypatch, skills_dir) -> None:
    """Point both the detector and the applier at the temp dirs.

    `config_apply` imports `CONTENT_TARGET_DIRS` by value, so patching only
    `config_collision` would leave the applier looking at the real ~/.claude.
    """
    dirs = {"skills": lambda: skills_dir, "agents": lambda: tmp_path}
    monkeypatch.setattr(config_collision, "CONTENT_TARGET_DIRS", dirs)
    monkeypatch.setattr(config_apply, "CONTENT_TARGET_DIRS", dirs)
    monkeypatch.setattr(config_apply, "claude_kit_repo_dir", lambda: CATALOG_DIR)


def _manually_place_fixture_skill(tmp_path, monkeypatch) -> Path:
    skills_dir = tmp_path / ".claude" / "skills"
    (skills_dir / "fixture-skill").mkdir(parents=True)
    (skills_dir / "fixture-skill" / "SKILL.md").write_text("hand-placed, not from claude-kit")
    _patch_dirs(tmp_path, monkeypatch, skills_dir)
    return skills_dir


def test_collision_is_detected_for_manually_placed_item(tmp_path, monkeypatch):
    _manually_place_fixture_skill(tmp_path, monkeypatch)
    registry = _registry()
    installed = _empty_installed()

    collisions = config_collision.detect_all_collisions(registry, installed)

    assert collisions == {"skills": {"fixture-skill"}}


def test_selection_refused_without_confirmation(tmp_path, monkeypatch):
    skills_dir = _manually_place_fixture_skill(tmp_path, monkeypatch)
    registry = _registry()
    installed = _empty_installed()

    desired = {**_EMPTY_SELECTION, "skills": {"fixture-skill"}}
    plan = compute_selection_diff(registry, installed, desired)

    errors = config_plan.apply_plan(plan, registry, installed, confirm_collision=lambda c, n: False)

    assert len(errors) == 1
    assert "fixture-skill" not in installed.skills
    # the manually-placed file must be left completely untouched
    assert (
        skills_dir / "fixture-skill" / "SKILL.md"
    ).read_text() == "hand-placed, not from claude-kit"


def test_selection_tracked_as_user_sourced_when_confirmed(tmp_path, monkeypatch):
    skills_dir = _manually_place_fixture_skill(tmp_path, monkeypatch)
    registry = _registry()
    installed = _empty_installed()

    desired = {**_EMPTY_SELECTION, "skills": {"fixture-skill"}}
    plan = compute_selection_diff(registry, installed, desired)

    errors = config_plan.apply_plan(plan, registry, installed, confirm_collision=lambda c, n: True)

    assert errors == []
    assert installed.skills["fixture-skill"].source == "user"
    assert (
        skills_dir / "fixture-skill" / "SKILL.md"
    ).read_text() == "hand-placed, not from claude-kit"


def test_no_collision_when_name_is_not_present_on_disk(tmp_path, monkeypatch):
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    _patch_dirs(tmp_path, monkeypatch, skills_dir)
    registry = _registry()
    installed = _empty_installed()

    collisions = config_collision.detect_all_collisions(registry, installed)

    assert collisions == {}
