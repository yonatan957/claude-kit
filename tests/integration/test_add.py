"""Integration test: `claude-kit add <type> <name>` installs with no picker
shown, drives Step 2 configure prompts when inputs are required, and exits 0
(FR-017/FR-019)."""

import json

from src.commands import add_remove_cmd, config_cmd
from src.core.state_model import PluginEntry


def test_add_content_component_no_picker_shown(cli_env):
    add_remove_cmd.run_add("skills", "fixture-skill")

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert "fixture-skill" in installed["skills"]
    assert (cli_env["skills_dir"] / "fixture-skill" / "SKILL.md").exists()


def test_add_script_component_with_inputs_configures_and_exits_zero(cli_env):
    add_remove_cmd.run_add("tools", "fixture-tool")  # exits 0 implicitly (no exception)

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    entry = installed["tools"]["fixture-tool"]
    assert entry["config"]["status"] == "done"
    assert entry["config"]["answers"] == {"api_endpoint": "<set>"}


def test_add_marketplace_component(cli_env, monkeypatch):
    calls = []

    def fake_install_plugin(name, component, commands):
        calls.append(name)
        return PluginEntry(
            source="claude-kit",
            marketplace=component.marketplace,
            version=component.version,
            enabled=True,
        )

    monkeypatch.setattr(config_cmd, "install_plugin", fake_install_plugin)

    add_remove_cmd.run_add("plugins", "fixture-plugin")

    assert calls == ["fixture-plugin"]
    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert installed["plugins"]["fixture-plugin"]["source"] == "claude-kit"
