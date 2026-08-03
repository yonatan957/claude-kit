"""Integration test: `claude-kit check` writes `state.json` with a non-null
`message` and matching `findings`, exits `0`, and produces no interactive
stdout (FR-028-FR-031)."""

import json

from src.commands import check_cmd
from src.installers.catalog_sync import SyncResult


def test_check_writes_non_null_message_and_matching_findings(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    installed_path = tmp_path / "installed.json"
    monkeypatch.setattr(check_cmd, "state_json_path", lambda: state_path)
    monkeypatch.setattr(check_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(check_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        check_cmd,
        "sync_catalog",
        lambda url, repo_dir=None: SyncResult(commit="newcommit", synced=True),
    )
    monkeypatch.setattr(check_cmd, "_latest_cli_version", lambda: "0.2.0")

    check_cmd.run_check()  # exits 0 implicitly (no exception raised)

    snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    assert snapshot["message"] is not None
    assert snapshot["findings"]["remote_commit"] == "newcommit"
    assert snapshot["findings"]["latest_cli_version"] == "0.2.0"
    assert "0.2.0" in snapshot["message"]

    captured = capsys.readouterr()
    assert captured.out == ""  # silent on success (Principle V / cli-commands.md)


def test_check_counts_pending_configurations(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    installed_path = tmp_path / "installed.json"
    installed_path.write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-08-03T00:00:00Z",
                "catalog_commit": "abc",
                "registry_version": "1.0.0",
                "cli_version": "0.1.0",
                "tools": {
                    "t1": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {"status": "pending", "verified_at": None, "answers": {}},
                    }
                },
                "mcps": {
                    "m1": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {"status": "pending", "verified_at": None, "answers": {}},
                    },
                    "m2": {
                        "source": "claude-kit",
                        "version": "1.0.0",
                        "installed_hash": "x",
                        "config": {
                            "status": "done",
                            "verified_at": "2026-08-03T00:00:00Z",
                            "answers": {},
                        },
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(check_cmd, "state_json_path", lambda: state_path)
    monkeypatch.setattr(check_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(check_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(
        check_cmd, "sync_catalog", lambda url, repo_dir=None: SyncResult(commit="abc", synced=True)
    )

    check_cmd.run_check()

    snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    assert snapshot["findings"]["pending_config_count"] == 2
