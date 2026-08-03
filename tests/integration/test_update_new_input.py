"""Integration test: an update that introduces a new required input marks
that component `"pending"` and lists it in the end-of-run summary, without
pausing (FR-024)."""

import json

from src.commands import update_cmd


def _build_catalog_with_new_required_input(tmp_path):
    catalog = tmp_path / "catalog"
    tool_dir = catalog / "tools" / "needs-new-input"
    tool_dir.mkdir(parents=True)
    (tool_dir / "config.sh").write_text(
        "#!/bin/sh\n"
        'if [ -z "$API_ENDPOINT" ] || [ -z "$API_TOKEN" ]; then\n'
        "  exit 1\n"
        "fi\n"
        "exit 0\n"
    )
    (tool_dir / "verify.sh").write_text("#!/bin/sh\nexit 0\n")

    registry_data = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "min_cli_version": "0.1.0",
        "types": [{"name": "tools", "handler": "script"}],
        "plugin_marketplace": {"add": "true", "install": "true", "update": "true", "remove": "true"},
        "tools": {
            "needs-new-input": {
                "description": "d",
                "handler": "script",
                "version": "1.0.0",
                "inputs": [
                    {"name": "api_endpoint", "label": "Endpoint", "secret": False},
                    {"name": "api_token", "label": "Token", "secret": False},  # newly required
                ],
            }
        },
    }
    (catalog / "registry.json").write_text(json.dumps(registry_data))
    return catalog


def test_update_new_required_input_marks_pending_without_pausing(update_env, monkeypatch, tmp_path):
    catalog = _build_catalog_with_new_required_input(tmp_path)
    monkeypatch.setattr(update_cmd, "claude_kit_repo_dir", lambda: catalog)
    monkeypatch.setattr(update_cmd, "registry_json_path", lambda: catalog / "registry.json")

    # Simulate a prior install from before "api_token" existed: stored at an
    # older version (so update sees it as outdated) with only the old answer.
    update_env["installed_path"].write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-01-01T00:00:00Z",
                "catalog_commit": "before",
                "registry_version": "0.9.0",
                "cli_version": "0.1.0",
                "tools": {
                    "needs-new-input": {
                        "source": "claude-kit",
                        "version": "0.9.0",
                        "installed_hash": "whatever",
                        "config": {"status": "done", "verified_at": "2026-01-01T00:00:00Z", "answers": {}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    update_env["env_dir"].mkdir(parents=True)
    (update_env["env_dir"] / "needs-new-input.env").write_text("api_endpoint=https://x\n")

    update_cmd.run_update()  # must not raise / must not pause for input

    installed = json.loads(update_env["installed_path"].read_text(encoding="utf-8"))
    entry = installed["tools"]["needs-new-input"]
    assert entry["config"]["status"] == "pending"
