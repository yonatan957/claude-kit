"""Integration test: `update` re-running `verify.sh` for a component whose
credential is no longer valid marks it `"pending"` again and reports it,
without pausing to collect a new value (FR-044)."""

import json

from src.commands import update_cmd

_CATALOG_COMMANDS = {"add": "true", "install": "true", "update": "true", "remove": "true"}


def _build_catalog_with_flaky_verify(tmp_path, verify_exit_code: int):
    catalog = tmp_path / "catalog"
    tool_dir = catalog / "mcps" / "flaky-mcp"
    tool_dir.mkdir(parents=True)
    (tool_dir / "config.sh").write_text("#!/bin/sh\nexit 0\n")
    (tool_dir / "verify.sh").write_text(f"#!/bin/sh\nexit {verify_exit_code}\n")

    registry_data = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "min_cli_version": "0.1.0",
        "types": [{"name": "mcps", "handler": "script"}],
        "plugin_marketplace": _CATALOG_COMMANDS,
        "mcps": {
            "flaky-mcp": {
                "description": "d",
                "handler": "script",
                "version": "1.0.0",
                "inputs": [{"name": "api_key", "label": "Key", "secret": True}],
                "mcp_config": {"command": "node", "args": ["server.js"]},
            }
        },
    }
    (catalog / "registry.json").write_text(json.dumps(registry_data))
    return catalog


def _seed_installed_done(update_env, version: str = "1.0.0"):
    update_env["installed_path"].write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-01-01T00:00:00Z",
                "catalog_commit": "before",
                "registry_version": "1.0.0",
                "cli_version": "0.1.0",
                "mcps": {
                    "flaky-mcp": {
                        "source": "claude-kit",
                        "version": version,
                        "installed_hash": "whatever",
                        "config": {
                            "status": "done",
                            "verified_at": "2026-01-01T00:00:00Z",
                            "answers": {"api_key": "<set>"},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    update_env["env_dir"].mkdir(parents=True)
    (update_env["env_dir"] / "flaky-mcp.env").write_text("api_key=revoked-but-still-there\n")
    update_env["settings_path"].parent.mkdir(parents=True)
    update_env["settings_path"].write_text(
        json.dumps({"mcpServers": {"flaky-mcp": {"command": "node", "args": ["server.js"]}}})
    )


def test_reverify_failure_marks_pending_and_reports_without_pausing(update_env, monkeypatch, tmp_path):
    catalog = _build_catalog_with_flaky_verify(tmp_path, verify_exit_code=1)  # credential now invalid
    monkeypatch.setattr(update_cmd, "claude_kit_repo_dir", lambda: catalog)
    monkeypatch.setattr(update_cmd, "registry_json_path", lambda: catalog / "registry.json")
    _seed_installed_done(update_env)

    update_cmd.run_update()  # must not raise / must not pause for input

    installed = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))
    entry = installed["mcps"]["flaky-mcp"]
    assert entry["config"]["status"] == "pending"  # not "failed" (FR-044, distinct from FR-042)

    # the credential itself is preserved (never re-prompted) even though it's invalid
    secret = (update_env["env_dir"] / "flaky-mcp.env").read_text(encoding="utf-8")
    assert "revoked-but-still-there" in secret


def test_reverify_success_keeps_status_done(update_env, monkeypatch, tmp_path):
    catalog = _build_catalog_with_flaky_verify(tmp_path, verify_exit_code=0)  # credential still valid
    monkeypatch.setattr(update_cmd, "claude_kit_repo_dir", lambda: catalog)
    monkeypatch.setattr(update_cmd, "registry_json_path", lambda: catalog / "registry.json")
    _seed_installed_done(update_env)

    update_cmd.run_update()

    installed = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))
    assert installed["mcps"]["flaky-mcp"]["config"]["status"] == "done"
