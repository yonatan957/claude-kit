"""Integration test: a finding already recorded in `announced` is not shown
again on a later hook read; a genuinely new finding after another `check`
run is still shown (FR-032/SC-009)."""

import json

from src.commands import check_cmd
from src.installers.catalog_sync import SyncResult
from src.notify import hook


def test_finding_not_repeated_until_something_new(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    installed_path = tmp_path / "installed.json"
    monkeypatch.setattr(check_cmd, "state_json_path", lambda: state_path)
    monkeypatch.setattr(check_cmd, "installed_json_path", lambda: installed_path)
    monkeypatch.setattr(check_cmd, "catalog_remote_url", lambda: "unused://fixture")
    monkeypatch.setattr(hook, "_state_json_path", lambda: state_path)

    # First check: a newer CLI version is found.
    monkeypatch.setattr(check_cmd, "_latest_cli_version", lambda: "0.2.0")
    monkeypatch.setattr(
        check_cmd, "sync_catalog", lambda url, repo_dir=None: SyncResult(commit="c1", synced=True)
    )
    check_cmd.run_check()

    hook.print_notice()
    first_output = capsys.readouterr().out
    assert "0.2.0" in first_output

    # Second check with identical findings: nothing new to announce.
    check_cmd.run_check()

    hook.print_notice()
    second_output = capsys.readouterr().out
    assert second_output == ""  # not repeated (FR-032/SC-009)

    # Third check: a genuinely new finding (newer catalog) appears.
    monkeypatch.setattr(
        check_cmd, "sync_catalog", lambda url, repo_dir=None: SyncResult(commit="c2", synced=True)
    )
    installed_path.write_text(
        json.dumps(
            {
                "state_version": "1",
                "last_updated": "2026-08-03T00:00:00Z",
                "catalog_commit": "c1",
                "registry_version": "1.0.0",
                "cli_version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    check_cmd.run_check()

    hook.print_notice()
    third_output = capsys.readouterr().out
    assert third_output != ""
    assert "0.2.0" not in third_output  # the CLI-version finding stays suppressed
    assert "newer catalog" in third_output.lower()
