"""Full-system idempotency pass (Principle IV): run the equivalent of
quickstart.md's Story 1-5 sequence twice end-to-end from the same populated
state, and diff installed.json/state.json/claude_settings.json. Nothing
should differ except timestamps — no duplicate entries, no duplicate
mcpServers registrations."""

import json
from pathlib import Path

import pytest

from src.commands import add_remove_cmd, check_cmd, config_cmd, list_cmd, update_cmd
from src.installers.catalog_sync import SyncResult

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


@pytest.fixture
def full_system_env(tmp_path, monkeypatch):
    installed_path = tmp_path / "installed.json"
    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"
    skills_dir = tmp_path / ".claude" / "skills"
    agents_dir = tmp_path / ".claude" / "agents"
    state_path = tmp_path / "state.json"

    for module in (config_cmd, update_cmd):
        monkeypatch.setattr(module, "installed_json_path", lambda: installed_path)
        monkeypatch.setattr(module, "claude_kit_repo_dir", lambda: CATALOG_DIR)
        monkeypatch.setattr(module, "claude_settings_path", lambda: settings_path)
        monkeypatch.setattr(module, "env_dir", lambda: env_dir)
        monkeypatch.setattr(module, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
        monkeypatch.setattr(module, "catalog_remote_url", lambda: "unused://fixture")
        monkeypatch.setattr(
            module,
            "sync_catalog",
            lambda url, repo_dir=None: SyncResult(commit="fixed-commit", synced=True),
        )
        monkeypatch.setattr(
            module, "_CONTENT_TARGET_DIRS", {"skills": lambda: skills_dir, "agents": lambda: agents_dir}
        )

    monkeypatch.setattr(
        config_cmd, "_collect_answers", lambda name, component: {i.name: "testval" for i in component.inputs}
    )

    monkeypatch.setattr(list_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(list_cmd, "registry_json_path", lambda: CATALOG_DIR / "registry.json")

    monkeypatch.setattr(check_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(check_cmd, "state_json_path", lambda: state_path)
    monkeypatch.setattr(check_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        check_cmd, "sync_catalog", lambda url, repo_dir=None: SyncResult(commit="fixed-commit", synced=True)
    )

    return {
        "installed_path": installed_path,
        "settings_path": settings_path,
        "state_path": state_path,
        "env_dir": env_dir,
    }


def _run_full_sequence() -> None:
    # Story 1/2: install a mix of components across every handler.
    add_remove_cmd.run_add("skills", "fixture-skill")
    add_remove_cmd.run_add("tools", "fixture-tool")
    add_remove_cmd.run_add("mcps", "fixture-mcp")
    # Story 3: sync/refresh.
    update_cmd.run_update()
    # Story 4: discover.
    list_cmd.run_list()
    # Story 5: background check.
    check_cmd.run_check()


def _strip_timestamps(data: dict) -> dict:
    stripped = dict(data)
    stripped.pop("last_updated", None)
    for category in ("skills", "agents", "plugins", "tools", "mcps"):
        for entry in stripped.get(category, {}).values():
            entry.pop("installed_at", None)
            if "config" in entry:
                entry["config"].pop("verified_at", None)
    return stripped


def test_full_sequence_twice_is_idempotent(full_system_env, capsys):
    _run_full_sequence()
    capsys.readouterr()  # discard first pass output

    installed_first = json.loads(full_system_env["installed_path"].read_text(encoding="utf-8"))
    settings_first = full_system_env["settings_path"].read_text(encoding="utf-8")

    _run_full_sequence()

    installed_second = json.loads(full_system_env["installed_path"].read_text(encoding="utf-8"))
    settings_second = full_system_env["settings_path"].read_text(encoding="utf-8")

    assert _strip_timestamps(installed_first) == _strip_timestamps(installed_second)
    assert settings_first == settings_second  # byte-identical, not just JSON-equivalent

    settings_json = json.loads(settings_second)
    assert list(settings_json.get("mcpServers", {}).keys()).count("fixture-mcp") == 1

    skill_files = list((Path(full_system_env["installed_path"]).parent / ".claude" / "skills" / "fixture-skill").iterdir())
    assert len(skill_files) == 1  # no duplicate file copies
