"""Integration test: `claude-kit add <type> <name>` on a name colliding with
an existing "user"-sourced entry is refused without explicit, distinct
confirmation (FR-043)."""

import json

import pytest
import typer

from src.commands import add_remove_cmd


def test_add_refuses_naming_collision_without_confirmation(cli_env, monkeypatch):
    skills_dir = cli_env["skills_dir"]
    (skills_dir / "fixture-skill").mkdir(parents=True)
    (skills_dir / "fixture-skill" / "SKILL.md").write_text("hand-placed, not from claude-kit")

    monkeypatch.setattr(add_remove_cmd, "_default_confirm_collision", lambda category, name: False)

    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_add("skills", "fixture-skill")

    assert exc_info.value.exit_code == 1
    assert (skills_dir / "fixture-skill" / "SKILL.md").read_text() == "hand-placed, not from claude-kit"
    if cli_env["installed_path"].exists():
        installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
        assert "fixture-skill" not in installed.get("skills", {})


def test_add_tracks_as_user_sourced_when_collision_confirmed(cli_env, monkeypatch):
    skills_dir = cli_env["skills_dir"]
    (skills_dir / "fixture-skill").mkdir(parents=True)
    (skills_dir / "fixture-skill" / "SKILL.md").write_text("hand-placed, not from claude-kit")

    monkeypatch.setattr(add_remove_cmd, "_default_confirm_collision", lambda category, name: True)

    add_remove_cmd.run_add("skills", "fixture-skill")

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert installed["skills"]["fixture-skill"]["source"] == "user"
    assert (skills_dir / "fixture-skill" / "SKILL.md").read_text() == "hand-placed, not from claude-kit"
