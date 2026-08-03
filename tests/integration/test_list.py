"""Integration test: `claude-kit list` shows every catalog component's
category, installed/not, current-vs-outdated, config status (done/pending/
failed/n-a), and active/inactive state, with pending visually distinguished
from done (FR-026/FR-027)."""

import json
from pathlib import Path

import pytest
import typer

from src.commands import list_cmd

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


@pytest.fixture
def list_env(tmp_path, monkeypatch):
    installed_path = tmp_path / "installed.json"
    monkeypatch.setattr(list_cmd, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
    monkeypatch.setattr(list_cmd, "installed_json_path", lambda: installed_path)
    return {"installed_path": installed_path}


def test_list_fails_clearly_when_no_local_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        list_cmd, "registry_json_path", lambda: tmp_path / "missing" / "registry.json"
    )

    with pytest.raises(typer.Exit) as exc_info:
        list_cmd.run_list()

    assert exc_info.value.exit_code == 1


def test_list_shows_every_component_with_correct_status(list_env, capsys):
    list_env["installed_path"].write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-08-03T00:00:00Z",
                "catalog_commit": "abc",
                "registry_version": "1.0.0",
                "cli_version": "0.1.0",
                "skills": {
                    "fixture-skill": {
                        "source": "claude-kit",
                        "installed_hash": "stale-hash",  # outdated vs. catalog content
                        "installed_at": "2026-08-03T00:00:00Z",
                    }
                },
                "tools": {
                    "fixture-tool": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {"status": "pending", "verified_at": None, "answers": {}},
                    }
                },
                "mcps": {
                    "fixture-mcp": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {
                            "status": "done",
                            "verified_at": "2026-08-03T00:00:00Z",
                            "answers": {},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    list_cmd.run_list()

    output = capsys.readouterr().out
    assert "fixture-skill" in output
    assert "outdated" in output  # stale hash vs. current catalog content
    assert "fixture-tool" in output
    assert "PENDING" in output  # visually distinct from "done"
    assert "fixture-mcp" in output
    assert "done" in output
    assert "fixture-plugin" in output  # in the catalog but never installed
    assert "no" in output  # fixture-plugin's "installed" column


def test_list_rows_reflect_installed_current_config_active(list_env):
    list_env["installed_path"].write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-08-03T00:00:00Z",
                "catalog_commit": "abc",
                "registry_version": "1.0.0",
                "cli_version": "0.1.0",
                "tools": {
                    "fixture-tool": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {
                            "status": "done",
                            "verified_at": "2026-08-03T00:00:00Z",
                            "answers": {},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    from src.core.registry import parse_registry

    registry = parse_registry((CATALOG_DIR / "registry.json").read_text(encoding="utf-8"))
    installed = list_cmd._load_installed()
    rows = list_cmd.build_rows(registry, installed)

    tool_row = next(r for r in rows if r["name"] == "fixture-tool")
    assert tool_row == {
        "category": "tools",
        "name": "fixture-tool",
        "installed": True,
        "current": True,
        "config": "done",
        "active": True,
    }

    mcp_row = next(r for r in rows if r["name"] == "fixture-mcp")
    assert mcp_row["installed"] is False
    assert mcp_row["current"] is None
    assert mcp_row["config"] == "n/a"
    assert mcp_row["active"] is False
