"""Integration test: the notify hook prints the stored `message` verbatim
with zero network/git/subprocess calls on that path (Principle V/FR-030/
FR-031)."""

import importlib
import json
import sys

from src.notify import hook


def test_hook_prints_message_verbatim(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"notice_version": "1", "message": "claude-kit: something worth knowing"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(hook, "_state_json_path", lambda: state_path)

    hook.print_notice()

    assert capsys.readouterr().out == "claude-kit: something worth knowing\n"


def test_hook_prints_nothing_when_message_is_null(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"notice_version": "1", "message": None}), encoding="utf-8")
    monkeypatch.setattr(hook, "_state_json_path", lambda: state_path)

    hook.print_notice()

    assert capsys.readouterr().out == ""


def test_hook_prints_nothing_when_state_json_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(hook, "_state_json_path", lambda: tmp_path / "does-not-exist.json")

    hook.print_notice()  # must not raise

    assert capsys.readouterr().out == ""


def test_hook_module_imports_no_core_or_installers():
    """subprocess IS imported (needed for the detached check launch, T058)
    but it is process management, not itself a network/git call — the
    forbidden set is specifically core/ and installers/, whose import graphs
    reach network/git/filesystem work synchronously."""
    for mod_name in [m for m in list(sys.modules) if m.startswith("src.notify")]:
        del sys.modules[mod_name]

    before = set(sys.modules.keys())
    importlib.import_module("src.notify.hook")
    after = set(sys.modules.keys())

    new_modules = after - before
    forbidden_prefixes = ("src.core", "src.installers")
    forbidden = [m for m in new_modules if m.startswith(forbidden_prefixes)]
    assert forbidden == []
    assert "socket" not in new_modules
