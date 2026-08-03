"""Integration test: `update` halts with a non-zero exit and applies no
changes when the catalog's `min_cli_version` exceeds the running CLI version
(FR-022)."""

import json

import pytest
import typer

from src.commands import update_cmd


def test_update_halts_when_min_cli_version_exceeds_running_version(
    update_env, monkeypatch, tmp_path
):
    high_version_catalog = tmp_path / "high_version_catalog"
    high_version_catalog.mkdir()
    registry_data = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "min_cli_version": "99.0.0",
        "types": [{"name": "skills", "handler": "content"}],
        "plugin_marketplace": {
            "add": "true",
            "install": "true",
            "update": "true",
            "remove": "true",
        },
    }
    registry_path = high_version_catalog / "registry.json"
    registry_path.write_text(json.dumps(registry_data))

    monkeypatch.setattr(update_cmd, "registry_json_path", lambda: registry_path)

    # Pre-existing state that must remain untouched.
    update_env["installed_path"].write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-01-01T00:00:00Z",
                "catalog_commit": "before",
                "registry_version": "0.9.0",
                "cli_version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    before = update_env["installed_path"].read_text(encoding="utf-8")

    with pytest.raises(typer.Exit) as exc_info:
        update_cmd.run_update()

    assert exc_info.value.exit_code == 1
    assert update_env["installed_path"].read_text(encoding="utf-8") == before
