"""Integration test: `update` syncs the catalog, refreshes installed
components, reuses existing credentials without re-prompting, and never reads
stdin (FR-021/FR-023)."""

import json
import sys

from src.commands import add_remove_cmd, update_cmd


class _StdinTripwire:
    """A stdin stand-in that fails the test if `update` ever touches it."""

    def read(self, *args, **kwargs):
        raise AssertionError("update must never read stdin")

    def readline(self, *args, **kwargs):
        raise AssertionError("update must never read stdin")

    def isatty(self):
        return False


def test_update_refreshes_outdated_component_and_reuses_secret(cli_env, update_env, monkeypatch):
    add_remove_cmd.run_add("mcps", "fixture-mcp")

    installed_before = json.loads(cli_env["installed_path"].read_text(encoding="utf-8"))
    installed_before["mcps"]["fixture-mcp"]["version"] = "0.0.1"  # simulate a stale install
    cli_env["installed_path"].write_text(json.dumps(installed_before), encoding="utf-8")

    secret_before = (cli_env["env_dir"] / "fixture-mcp.env").read_text(encoding="utf-8")

    monkeypatch.setattr(sys, "stdin", _StdinTripwire())

    update_cmd.run_update()

    installed_after = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))
    entry = installed_after["mcps"]["fixture-mcp"]
    assert entry["version"] == "1.0.0"
    assert entry["config"]["status"] == "done"

    secret_after = (update_env["env_dir"] / "fixture-mcp.env").read_text(encoding="utf-8")
    assert secret_after == secret_before  # credential preserved, never re-prompted


def test_update_is_a_no_op_when_nothing_is_outdated(cli_env, update_env, monkeypatch):
    add_remove_cmd.run_add("skills", "fixture-skill")
    monkeypatch.setattr(sys, "stdin", _StdinTripwire())

    update_cmd.run_update()  # must not raise even though nothing needs refreshing

    installed = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))
    assert "fixture-skill" in installed["skills"]
