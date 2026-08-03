"""Integration test: `claude-kit list` shows ONLY installed components
(FR-026), each with its category, version, current-vs-outdated freshness,
config status, and active state, with pending visually distinct (FR-027).

Catalog components that were never installed must not appear at all — that is
the behavior change this suite exists to lock in.
"""

import json
from pathlib import Path

import pytest
import typer

from src.commands import list_cmd
from src.core.registry import parse_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()

_BASE_STATE = {
    "state_version": "1",
    "last_updated": "2026-08-03T00:00:00Z",
    "catalog_commit": "abc",
    "registry_version": "1.0.0",
    "cli_version": "0.1.0",
}

_SKILL = {
    "source": "claude-kit",
    "installed_hash": "stale-hash",  # outdated vs. current catalog content
    "installed_at": "2026-08-03T00:00:00Z",
}
_PENDING_TOOL = {
    "source": "claude-kit",
    "version": "1.0.0",
    "installed_hash": "x",
    "config": {"status": "pending", "verified_at": None, "answers": {}},
}
_DONE_MCP = {
    "source": "claude-kit",
    "version": "1.0.0",
    "installed_hash": "x",
    "config": {"status": "done", "verified_at": "2026-08-03T00:00:00Z", "answers": {}},
}


@pytest.fixture
def list_env(tmp_path, monkeypatch):
    installed_path = tmp_path / "installed.json"
    monkeypatch.setattr(list_cmd, "registry_json_path", lambda: CATALOG_DIR / "registry.json")
    monkeypatch.setattr(list_cmd, "installed_json_path", lambda: installed_path)
    return {"installed_path": installed_path}


def write_installed(list_env, **categories) -> None:
    list_env["installed_path"].write_text(
        json.dumps({**_BASE_STATE, **categories}), encoding="utf-8"
    )


def registry():
    return parse_registry((CATALOG_DIR / "registry.json").read_text(encoding="utf-8"))


def test_list_fails_clearly_when_no_local_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        list_cmd, "registry_json_path", lambda: tmp_path / "missing" / "registry.json"
    )

    with pytest.raises(typer.Exit) as exc_info:
        list_cmd.run_list()

    assert exc_info.value.exit_code == 1


def test_list_shows_installed_components_with_correct_status(list_env, capsys):
    write_installed(
        list_env,
        skills={"fixture-skill": _SKILL},
        tools={"fixture-tool": _PENDING_TOOL},
        mcps={"fixture-mcp": _DONE_MCP},
    )

    list_cmd.run_list()

    output = capsys.readouterr().out
    assert "fixture-skill" in output
    assert "outdated" in output  # stale hash vs. current catalog content
    assert "fixture-tool" in output
    assert "PENDING" in output  # visually distinct from "done" (FR-027)
    assert "fixture-mcp" in output
    assert "done" in output


def test_catalog_only_components_are_never_listed(list_env, capsys):
    """FR-026: the whole point of the change — `fixture-plugin` exists in the
    catalog but was never installed, so it must not appear."""
    write_installed(list_env, skills={"fixture-skill": _SKILL})

    list_cmd.run_list()

    output = capsys.readouterr().out
    assert "fixture-skill" in output
    assert "fixture-plugin" not in output
    assert "fixture-tool" not in output
    assert "fixture-mcp" not in output
    assert "INSTALLED" not in output  # the column is gone


def test_orphaned_installed_component_is_listed_as_unknown(list_env, capsys):
    """Installed but absent from the catalog: still shown, freshness unknown.
    Hiding it would conceal something the developer actually has on disk."""
    write_installed(list_env, tools={"ghost-tool": _PENDING_TOOL})

    list_cmd.run_list()

    output = capsys.readouterr().out
    assert "ghost-tool" in output
    assert "unknown" in output


def test_empty_state_is_explicit_and_exits_zero(list_env, capsys):
    write_installed(list_env)

    list_cmd.run_list()  # must not raise

    assert list_cmd.EMPTY_MESSAGE in capsys.readouterr().out


def test_missing_installed_json_is_also_an_empty_state(list_env, capsys):
    list_cmd.run_list()  # installed.json was never written

    assert list_cmd.EMPTY_MESSAGE in capsys.readouterr().out


def test_rows_reflect_version_freshness_config_and_active(list_env):
    write_installed(list_env, tools={"fixture-tool": _DONE_MCP})

    rows = list_cmd.build_rows(registry(), list_cmd._load_installed())

    assert rows == [
        {
            "category": "tools",
            "name": "fixture-tool",
            "version": "1.0.0",
            "current": True,
            "config": "done",
            "active": True,
        }
    ]


def test_orphan_row_reports_current_as_none(list_env):
    write_installed(list_env, tools={"ghost-tool": _DONE_MCP})

    rows = list_cmd.build_rows(registry(), list_cmd._load_installed())

    assert rows[0]["current"] is None
    assert rows[0]["name"] == "ghost-tool"
