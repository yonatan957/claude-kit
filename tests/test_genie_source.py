"""``GenieSource``: what it asks, what it runs and in which order, and what it never lets out."""

import json
from pathlib import Path

import pytest
from fakes import FakePrompter, FakeRunner

from claude_kit.components import ComponentKind
from claude_kit.helpers import (
    CLAUDE_KIT_HOME,
    Conflict,
    SourceError,
    SourceUnreachable,
    UsageError,
)
from claude_kit.sources import GenieSource

GENIE_DIR = Path(__file__).parent / "data" / "genie"
MANIFEST_FILE = GENIE_DIR / "manifest.json"
TOKEN = "glpat-very-secret-0123"
ANSWERS = {"GITLAB_TOKEN": TOKEN, "KUBECONFIG": "~/.kube/config"}
MCP = ComponentKind.MCP
TOOL = ComponentKind.TOOL


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for key in ("GITLAB_TOKEN", "GITLAB_URL", "KUBECONFIG"):
        monkeypatch.delenv(key, raising=False)


def build_source(
    runner: FakeRunner | None = None,
    prompter: FakePrompter | None = None,
    genie_dir: Path = GENIE_DIR,
) -> GenieSource:
    return GenieSource(
        genie_dir=genie_dir,
        prompter=prompter or FakePrompter(ANSWERS),
        runner=runner or FakeRunner(),
    )


def added_config(runner: FakeRunner) -> dict:
    for call in runner.calls:
        if call.command[2:3] == ["add-json"]:
            return json.loads(call.command[4])
    raise AssertionError("add-json was never called")


def test_nothing_is_loaded_until_genie_is_asked_for_its_own_kinds(tmp_path):
    (tmp_path / "manifest.json").write_text("{ not json", encoding="utf-8")
    source = GenieSource(genie_dir=tmp_path)
    assert source.kinds == frozenset({MCP, TOOL})
    assert source.install(ComponentKind.SKILL, "gitlab") == []
    with pytest.raises(SourceError):
        source.search(MCP)


@pytest.mark.parametrize("genie_dir, name", [(GENIE_DIR, "ghost"), (None, "gitlab")])
def test_what_genie_does_not_have_answers_empty_and_runs_nothing(
    tmp_path, genie_dir, name
):
    """``None`` is a kit home with no local copy: ``ck init`` never ran."""
    runner, prompter = FakeRunner(), FakePrompter()
    source = build_source(runner, prompter, genie_dir or tmp_path)
    assert source.search(MCP, name) == []
    assert source.install(MCP, name) == []
    assert source.uninstall(MCP, name) == []
    assert runner.calls == []
    assert prompter.asked == []


def test_search_answers_components_from_genie():
    found = build_source().search(MCP)
    assert [(one.name, one.version, one.source) for one in found] == [
        ("gitlab", "1.2.0", "genie"),
        ("k8s", "2.0.1", "genie"),
    ]


def test_an_mcp_only_entry_is_registered_in_user_scope_with_placeholders_filled():
    runner = FakeRunner()
    installed = build_source(runner).install(MCP, "gitlab")

    assert [(one.name, one.source, one.version) for one in installed] == [
        ("gitlab", "genie", "1.2.0")
    ]
    assert runner.steps == ["get", "add-json"]
    assert runner.calls[1].command[-2:] == ["--scope", "user"]
    assert added_config(runner) == {
        "type": "http",
        "url": "https://gitlab.internal/mcp",
        "headers": {"Authorization": f"Bearer {TOKEN}"},
    }


def test_a_tool_runs_its_script_with_the_inputs_in_its_env_and_never_calls_claude():
    runner = FakeRunner()
    build_source(runner).install(TOOL, "kubectl")
    assert runner.steps == ["install"]
    env = runner.calls[0].env
    assert env["GENIE_NAME"] == "kubectl"
    assert env["GENIE_VERSION"] == "1.31.2"
    assert env["CLAUDE_KIT_HOME"] == str(CLAUDE_KIT_HOME)


def test_a_tool_and_mcp_entry_runs_the_script_then_registers_it():
    runner = FakeRunner()
    build_source(runner).install(MCP, "k8s")
    assert runner.steps == ["get", "install", "add-json"]
    assert runner.calls[1].env["KUBECONFIG"] == "~/.kube/config"
    assert added_config(runner)["command"] == f"{CLAUDE_KIT_HOME}/tools/k8s-mcp/k8s-mcp"


def test_a_tool_and_mcp_entry_is_unregistered_before_its_binary_is_removed():
    runner = FakeRunner(registered={"k8s"})
    removed = build_source(runner).uninstall(MCP, "k8s")
    assert [one.name for one in removed] == ["k8s"]
    assert runner.steps == ["remove", "uninstall"]


def test_uninstalling_an_mcp_only_entry_that_is_not_registered_answers_empty():
    assert build_source().uninstall(MCP, "gitlab") == []


def test_a_failed_install_script_is_a_source_error_and_registers_nothing():
    runner = FakeRunner(failing={"install": "download failed"})
    with pytest.raises(SourceError) as raised:
        build_source(runner).install(MCP, "k8s")
    assert "download failed" in str(raised.value)
    assert runner.steps == ["get", "install"]


def test_force_removes_the_old_registration_then_adds():
    runner = FakeRunner(registered={"gitlab"})
    build_source(runner).install(MCP, "gitlab", force=True)
    assert runner.steps == ["get", "remove", "add-json"]


def test_an_mcp_already_registered_is_a_conflict_before_anything_is_asked():
    runner, prompter = FakeRunner(registered={"gitlab"}), FakePrompter(ANSWERS)
    with pytest.raises(Conflict):
        build_source(runner, prompter).install(MCP, "gitlab")
    assert runner.steps == ["get"]
    assert prompter.asked == []


def test_claude_not_on_path_is_unreachable_before_any_script_runs():
    source = build_source(FakeRunner(claude_missing=True))
    with pytest.raises(SourceUnreachable):
        source.install(MCP, "k8s")
    with pytest.raises(SourceUnreachable):
        source.uninstall(MCP, "gitlab")


def test_the_token_never_appears_in_a_command_label_or_an_error():
    runner = FakeRunner(failing={"add-json": f"rejected header Bearer {TOKEN}"})
    with pytest.raises(SourceError) as raised:
        build_source(runner).install(MCP, "gitlab")
    assert TOKEN not in str(raised.value)
    assert "***" in str(raised.value)
    assert all(TOKEN not in call.label for call in runner.calls)


def test_a_value_already_in_the_environment_is_offered_and_used(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "from-env")
    runner, prompter = FakeRunner(), FakePrompter()
    build_source(runner, prompter).install(MCP, "gitlab")
    assert ("GITLAB_TOKEN", "from-env") in prompter.asked
    assert added_config(runner)["headers"]["Authorization"] == "Bearer from-env"


def test_a_required_input_left_empty_is_a_usage_error_and_nothing_runs():
    runner = FakeRunner()
    with pytest.raises(UsageError) as raised:
        build_source(runner, FakePrompter()).install(MCP, "k8s")
    assert "KUBECONFIG" in str(raised.value)
    assert runner.steps == ["get"]


def test_an_unknown_placeholder_fails_before_any_script_runs(tmp_path):
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["entries"][1]["mcp"]["command"] = "{K8S_HOME}/k8s-mcp"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    runner = FakeRunner()
    with pytest.raises(SourceError) as raised:
        build_source(runner, genie_dir=tmp_path).install(MCP, "k8s")
    assert "unknown placeholder K8S_HOME" in str(raised.value)
    assert runner.steps == ["get"]
