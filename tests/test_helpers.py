"""``run``: the env it adds and the label it reports."""

import subprocess

import pytest

from claude_kit.helpers import system


@pytest.fixture
def spawned(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(system, "find_binary", lambda name: f"/bin/{name}")
    monkeypatch.setattr(system.subprocess, "run", fake_run)
    return calls


def test_run_adds_env_on_top_of_the_current_environment(monkeypatch, spawned):
    monkeypatch.setenv("ALREADY_THERE", "kept")
    system.run(["tool"], env={"GITLAB_TOKEN": "secret"})
    env = spawned[0]["env"]
    assert env["GITLAB_TOKEN"] == "secret"
    assert env["ALREADY_THERE"] == "kept"


def test_run_without_env_inherits_the_environment_untouched(spawned):
    system.run(["tool"])
    assert spawned[0]["env"] is None


def test_a_label_replaces_the_command_in_the_result(spawned):
    result = system.run(
        ["claude", "mcp", "add-json", "x", '{"token": "secret"}'],
        label="claude mcp add-json x",
    )
    assert result.command == "claude mcp add-json x"


def test_without_a_label_the_result_names_the_command(spawned):
    assert system.run(["tool", "--flag"]).command == "tool --flag"
