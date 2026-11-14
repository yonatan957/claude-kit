from pathlib import Path

import pytest
from conftest import build_component
from fakes import FakePrompter, FakeRunner, FakeSource
from typer.testing import CliRunner

from claude_kit import cli
from claude_kit.components import ComponentKind
from claude_kit.helpers import (
    Conflict,
    ExitCode,
    KitError,
    NotFound,
    Refused,
    RolledBack,
    SourceError,
    SourceUnreachable,
    UsageError,
)
from claude_kit.sources import GenieSource

runner = CliRunner()

REVIEWER = build_component(name="code-reviewer", source="skillhub")


GENIE_MANIFEST = Path(__file__).parent / "data" / "genie" / "manifest.json"


def use_sources(monkeypatch, replaced):
    monkeypatch.setattr("claude_kit.services.install_service.AVAILABLE_SOURCES", replaced)
    monkeypatch.setattr("claude_kit.services.search_service.AVAILABLE_SOURCES", replaced)
    monkeypatch.setattr(
        "claude_kit.services.uninstall_service.AVAILABLE_SOURCES", replaced
    )
    return replaced


@pytest.fixture
def sources(monkeypatch):
    return use_sources(monkeypatch, [FakeSource("skillhub", [REVIEWER])])


@pytest.fixture
def claude() -> FakeRunner:
    return FakeRunner()


@pytest.fixture
def genie_first(monkeypatch, claude):
    genie = GenieSource(
        genie_dir=GENIE_MANIFEST.parent,
        prompter=FakePrompter({"GITLAB_TOKEN": "glpat-secret"}),
        runner=claude,
    )
    return use_sources(monkeypatch, [genie, FakeSource("skillhub", [REVIEWER])])


def test_version_prints_and_exits_clean():
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == ExitCode.OK
    assert "claude-kit" in result.stdout


def test_an_unknown_kind_is_a_usage_error():
    result = runner.invoke(cli.app, ["search", "hook", "anything"])
    assert result.exit_code == ExitCode.USAGE


def test_an_unknown_command_is_a_usage_error():
    result = runner.invoke(cli.app, ["publish"])
    assert result.exit_code == ExitCode.USAGE


def test_search_prints_what_a_source_answered(sources):
    result = runner.invoke(cli.app, ["search", "skill", ""])
    assert result.exit_code == ExitCode.OK
    assert "code-reviewer" in result.stdout


def test_installing_something_no_source_has_is_not_found(sources, kit_home):
    result = runner.invoke(
        cli.app, ["install", "skill", "ghost", "--home", str(kit_home)]
    )
    assert result.exit_code == ExitCode.NOT_FOUND


def test_uninstalling_something_that_is_not_there_is_not_found(sources, kit_home):
    result = runner.invoke(
        cli.app, ["uninstall", "skill", "ghost", "--home", str(kit_home)]
    )
    assert result.exit_code == ExitCode.NOT_FOUND


def test_install_reports_the_source_it_used(sources, kit_home):
    result = runner.invoke(
        cli.app, ["install", "skill", "code-reviewer", "--home", str(kit_home)]
    )
    assert result.exit_code == ExitCode.OK
    assert "skillhub" in result.stdout


def test_list_shows_an_install_until_it_is_uninstalled(sources, kit_home):
    home = ["--home", str(kit_home)]
    runner.invoke(cli.app, ["install", "skill", "code-reviewer", *home])
    assert "code-reviewer" in runner.invoke(cli.app, ["list", *home]).stdout

    runner.invoke(cli.app, ["uninstall", "skill", "code-reviewer", *home])
    assert "nothing installed" in runner.invoke(cli.app, ["list", *home]).stdout


def test_installing_twice_is_a_conflict(sources, kit_home):
    install = ["install", "skill", "code-reviewer", "--home", str(kit_home)]
    runner.invoke(cli.app, install)
    result = runner.invoke(cli.app, install)
    assert isinstance(result.exception, Conflict)


def test_list_without_a_kit_exits_not_found(tmp_path):
    result = runner.invoke(cli.app, ["list", "--home", str(tmp_path / "absent")])
    assert result.exit_code == ExitCode.FAILURE
    assert isinstance(result.exception, KitError)


@pytest.mark.parametrize(
    "failure, code",
    [
        (UsageError("addressed wrongly"), ExitCode.USAGE),
        (NotFound("no such thing"), ExitCode.NOT_FOUND),
        (SourceError("genie", "rejected"), ExitCode.FAILURE),
        (SourceUnreachable("genie", "no network"), ExitCode.UNREACHABLE),
        (Refused("you declined"), ExitCode.REFUSED),
        (Conflict("two of those"), ExitCode.CONFLICT),
        (RolledBack("undid everything"), ExitCode.ROLLED_BACK),
        (KitError("something nobody anticipated"), ExitCode.FAILURE),
    ],
)
def test_run_exits_with_the_code_that_belongs_to_the_error(monkeypatch, failure, code):
    def raising() -> None:
        raise failure

    monkeypatch.setattr(cli, "app", raising)
    with pytest.raises(SystemExit) as raised:
        cli.run()
    assert raised.value.code == code


def test_every_kind_is_a_word_the_cli_accepts():
    for kind in ComponentKind:
        result = runner.invoke(cli.app, ["search", str(kind), "--help"])
        assert result.exit_code == ExitCode.OK


def test_an_mcp_from_genie_is_installed_listed_and_uninstalled(genie_first, claude, kit_home):
    home = ["--home", str(kit_home)]
    installed = runner.invoke(cli.app, ["install", "mcp", "gitlab", *home])
    assert installed.exit_code == ExitCode.OK
    assert "genie" in installed.stdout
    assert "gitlab" in claude.registered

    listed = runner.invoke(cli.app, ["list", *home]).stdout
    assert "gitlab" in listed and "genie" in listed

    removed = runner.invoke(cli.app, ["uninstall", "mcp", "gitlab", *home])
    assert removed.exit_code == ExitCode.OK
    assert "gitlab" not in claude.registered
    assert "nothing installed" in runner.invoke(cli.app, ["list", *home]).stdout


def test_a_skill_still_reaches_skillhub_with_genie_first(genie_first, claude, kit_home):
    result = runner.invoke(
        cli.app, ["install", "skill", "code-reviewer", "--home", str(kit_home)]
    )
    assert result.exit_code == ExitCode.OK
    assert "skillhub" in result.stdout
    assert claude.calls == []


def test_search_lists_genie_mcps(genie_first):
    result = runner.invoke(cli.app, ["search", "mcp", ""])
    assert "gitlab" in result.stdout and "k8s" in result.stdout


def test_the_token_is_nowhere_in_the_kit_home(genie_first, kit_home):
    runner.invoke(cli.app, ["install", "mcp", "gitlab", "--home", str(kit_home)])
    for path in kit_home.rglob("*"):
        if path.is_file():
            assert b"glpat-secret" not in path.read_bytes()
