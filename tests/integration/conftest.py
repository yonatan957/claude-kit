"""Shared fixtures for command-level integration tests (Phase 4+)."""

from pathlib import Path

import pytest

from src.commands import config_cmd, update_cmd
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
    """Isolates config_cmd's (and, transitively, add_remove_cmd's) filesystem
    targets under tmp_path, and stubs the catalog sync to use the local
    fixture Catalog Repo directly rather than a real git clone/pull."""
    paths = _isolated_paths(tmp_path)

    monkeypatch.setattr(config_cmd, "installed_json_path", lambda: paths["installed_path"])
    monkeypatch.setattr(config_cmd, "claude_kit_repo_dir", lambda: CATALOG_DIR)
    monkeypatch.setattr(config_cmd, "claude_settings_path", lambda: paths["settings_path"])
    monkeypatch.setattr(config_cmd, "env_dir", lambda: paths["env_dir"])
    monkeypatch.setattr(
        config_cmd,
        "_CONTENT_TARGET_DIRS",
        {"skills": lambda: paths["skills_dir"], "agents": lambda: paths["agents_dir"]},
    )
    monkeypatch.setattr(config_cmd, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
    monkeypatch.setattr(config_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        config_cmd,
        "sync_catalog",
        lambda url, repo_dir=None: SyncResult(commit="fixture-commit", synced=True),
    )
    monkeypatch.setattr(
        config_cmd, "_collect_answers", lambda name, component: {i.name: "testval" for i in component.inputs}
    )

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
