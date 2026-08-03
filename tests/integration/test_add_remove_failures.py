"""Integration test: add/remove failures (unknown name, failing lifecycle
script) exit non-zero with a clear message and leave no partial/unlabeled
state behind (FR-020)."""

import json

import pytest
import typer

from src.commands import add_remove_cmd, config_cmd


def test_add_unknown_name_fails_non_zero(cli_env):
    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_add("tools", "not-a-real-tool")

    assert exc_info.value.exit_code == 1
    assert not cli_env["installed_path"].exists()


def test_add_unknown_category_fails_non_zero(cli_env):
    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_add("not-a-real-category", "fixture-tool")

    assert exc_info.value.exit_code == 1


def test_remove_unknown_category_fails_non_zero(cli_env):
    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_remove("not-a-real-category", "fixture-tool")

    assert exc_info.value.exit_code == 1


def test_remove_unknown_name_not_in_catalog_or_installed_fails_non_zero(cli_env):
    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_remove("tools", "not-a-real-tool")

    assert exc_info.value.exit_code == 1


def test_add_failing_lifecycle_script_fails_non_zero_and_leaves_no_state(tmp_path, monkeypatch, cli_env):
    broken_catalog = tmp_path / "broken_catalog"
    (broken_catalog / "tools" / "broken-tool").mkdir(parents=True)
    (broken_catalog / "tools" / "broken-tool" / "install.sh").write_text("#!/bin/sh\nexit 1\n")
    registry_data = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "min_cli_version": "0.1.0",
        "types": [{"name": "tools", "handler": "script"}],
        "plugin_marketplace": {"add": "true", "install": "true", "update": "true", "remove": "true"},
        "tools": {"broken-tool": {"description": "d", "handler": "script", "version": "1.0.0"}},
    }
    registry_path = broken_catalog / "registry.json"
    registry_path.write_text(json.dumps(registry_data))

    monkeypatch.setattr(config_cmd, "claude_kit_repo_dir", lambda: broken_catalog)
    monkeypatch.setattr(config_cmd, "registry_json_path", lambda: registry_path)

    with pytest.raises(typer.Exit) as exc_info:
        add_remove_cmd.run_add("tools", "broken-tool")

    assert exc_info.value.exit_code == 1
    # installed.json is still written (last_updated bookkeeping only happens
    # on success), so no partial/unlabeled entry for the failed component:
    if cli_env["installed_path"].exists():
        installed = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
        assert "broken-tool" not in installed.get("tools", {})
