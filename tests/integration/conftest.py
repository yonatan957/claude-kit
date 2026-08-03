"""Shared fixtures for command-level integration tests (Phase 4+)."""

from pathlib import Path

import pytest

from src.commands import config_apply, config_collision, config_state, update_cmd
from src.installers.catalog_sync import SyncResult

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


def _isolated_paths(tmp_path: Path) -> dict:
    return {
        "installed_path": tmp_path / "installed.json",
        "settings_path": tmp_path / ".claude" / "settings.json",
        "env_dir": tmp_path / ".claude-kit" / "env.d",
        "skills_dir": tmp_path / ".claude" / "skills",
        "agents_dir": tmp_path / ".claude" / "agents",
    }


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Isolates the config flow's (and, transitively, add_remove_cmd's)
    filesystem targets under tmp_path, and stubs the catalog sync to use the
    local fixture Catalog Repo directly rather than a real git clone/pull.

    The config flow spans several modules since the Phase 2 split, and each
    imports its path helpers by value — so every module that *uses* a name has
    to be patched, not just the one that defines it.
    """
    paths = _isolated_paths(tmp_path)
    content_dirs = {
        "skills": lambda: paths["skills_dir"],
        "agents": lambda: paths["agents_dir"],
    }

    # State I/O: installed.json, the catalog cache, and the sync stub.
    monkeypatch.setattr(config_state, "installed_json_path", lambda: paths["installed_path"])
    monkeypatch.setattr(config_state, "claude_kit_repo_dir", lambda: CATALOG_DIR)
    monkeypatch.setattr(config_state, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
    monkeypatch.setattr(config_state, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        config_state,
        "sync_catalog",
        lambda url, repo_dir=None: SyncResult(commit="fixture-commit", synced=True),
    )

    # Install/remove dispatch: where components land and how inputs are answered.
    monkeypatch.setattr(config_apply, "claude_kit_repo_dir", lambda: CATALOG_DIR)
    monkeypatch.setattr(config_apply, "claude_settings_path", lambda: paths["settings_path"])
    monkeypatch.setattr(config_apply, "env_dir", lambda: paths["env_dir"])
    monkeypatch.setattr(config_apply, "CONTENT_TARGET_DIRS", content_dirs)
    monkeypatch.setattr(
        config_apply,
        "collect_answers",
        lambda name, component: {i.name: "testval" for i in component.inputs},
    )

    # Collision detection reads the same locations independently.
    monkeypatch.setattr(config_collision, "CONTENT_TARGET_DIRS", content_dirs)
    monkeypatch.setattr(config_collision, "claude_settings_path", lambda: paths["settings_path"])

    return paths


@pytest.fixture
def update_env(tmp_path, monkeypatch):
    """Same isolated tmp_path layout as `cli_env`, but wired into update_cmd's
    module-level names. A test can add a component via add_remove_cmd (with
    `cli_env`) and then refresh it via update_cmd (with this fixture) against
    the same on-disk state by requesting both fixtures together."""
    paths = _isolated_paths(tmp_path)

    monkeypatch.setattr(update_cmd, "installed_json_path", lambda: paths["installed_path"])
    monkeypatch.setattr(update_cmd, "claude_kit_repo_dir", lambda: CATALOG_DIR)
    monkeypatch.setattr(update_cmd, "claude_settings_path", lambda: paths["settings_path"])
    monkeypatch.setattr(update_cmd, "env_dir", lambda: paths["env_dir"])
    monkeypatch.setattr(
        update_cmd,
        "_CONTENT_TARGET_DIRS",
        {"skills": lambda: paths["skills_dir"], "agents": lambda: paths["agents_dir"]},
    )
    monkeypatch.setattr(update_cmd, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
    monkeypatch.setattr(update_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        update_cmd,
        "sync_catalog",
        lambda url, repo_dir=None: SyncResult(commit="fixture-commit", synced=True),
    )

    return paths
