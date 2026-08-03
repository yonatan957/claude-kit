"""Integration test: running `update` twice consecutively with an unchanged
catalog produces a byte-identical `installed.json` (aside from timestamps)
(FR-025/Principle IV)."""

import json

from src.commands import add_remove_cmd, update_cmd


def _strip_timestamps(data: dict) -> dict:
    stripped = dict(data)
    stripped.pop("last_updated", None)
    for category in ("skills", "agents", "plugins", "tools", "mcps"):
        for entry in stripped.get(category, {}).values():
            entry.pop("installed_at", None)
            if "config" in entry:
                entry["config"].pop("verified_at", None)
    return stripped


def test_update_twice_is_idempotent(cli_env, update_env):
    add_remove_cmd.run_add("skills", "fixture-skill")
    add_remove_cmd.run_add("mcps", "fixture-mcp")

    update_cmd.run_update()
    first = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))

    update_cmd.run_update()
    second = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))

    assert _strip_timestamps(first) == _strip_timestamps(second)
