"""Integration test: `claude-kit remove <type> <name>` removes all
files/registrations and is a no-op success (exit 0) when run a second time
(FR-018/FR-037)."""

import json

from src.commands import add_remove_cmd


def test_remove_content_component(cli_env):
    add_remove_cmd.run_add("skills", "fixture-skill")

    add_remove_cmd.run_remove("skills", "fixture-skill")

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert "fixture-skill" not in installed["skills"]
    assert not (cli_env["skills_dir"] / "fixture-skill").exists()


def test_remove_script_component_deregisters_mcp_server(cli_env):
    add_remove_cmd.run_add("mcps", "fixture-mcp")

    add_remove_cmd.run_remove("mcps", "fixture-mcp")

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert "fixture-mcp" not in installed["mcps"]
    settings = json.loads(cli_env["settings_path"].read_text(encoding="utf-8"))
    assert "fixture-mcp" not in settings.get("mcpServers", {})
    assert not (cli_env["env_dir"] / "fixture-mcp.env").exists()


def test_remove_twice_is_idempotent_no_op(cli_env):
    add_remove_cmd.run_add("tools", "fixture-tool")
    add_remove_cmd.run_remove("tools", "fixture-tool")

    add_remove_cmd.run_remove("tools", "fixture-tool")  # must not raise

    installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    assert "fixture-tool" not in installed["tools"]


def test_remove_never_installed_component_is_a_no_op(cli_env):
    add_remove_cmd.run_remove("tools", "fixture-tool")  # never added; must not raise
