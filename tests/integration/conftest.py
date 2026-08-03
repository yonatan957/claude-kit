"""Shared fixtures for command-level integration tests (Phase 4+)."""

from pathlib import Path

import pytest

from src.commands import config_cmd
from src.installers.catalog_sync import SyncResult

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Isolates config_cmd's (and, transitively, add_remove_cmd's) filesystem
    targets under tmp_path, and stubs the catalog sync to use the local
    fixture Catalog Repo directly rather than a real git clone/pull."""
    installed_path = tmp_path / "installed.json"
    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"
    skills_dir = tmp_path / ".claude" / "skills"
    agents_dir = tmp_path / ".claude" / "agents"

    monkeypatch.setattr(config_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(config_cmd, "claude_kit_repo_dir", lambda: CATALOG_DIR)
    monkeypatch.setattr(config_cmd, "claude_settings_path", lambda: settings_path)
    monkeypatch.setattr(config_cmd, "env_dir", lambda: env_dir)
    monkeypatch.setattr(
        config_cmd, "_CONTENT_TARGET_DIRS", {"skills": lambda: skills_dir, "agents": lambda: agents_dir}
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

    return {
        "installed_path": installed_path,
        "settings_path": settings_path,
        "env_dir": env_dir,
        "skills_dir": skills_dir,
        "agents_dir": agents_dir,
    }
