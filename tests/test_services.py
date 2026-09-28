import pytest
from conftest import build_component
from fakes import FakeSource

from claude_kit import services
from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import (
    CLAUDE_KIT_HOME,
    DATABASE_FILE_NAME,
    STATE_FILE_NAME,
    ExitCode,
    KitNotFound,
    SourceUnreachable,
    Tool,
    ToolReport,
    ToolStatus,
    UsageError,
)
from claude_kit.storage import KitState, VersionStatus, write_state

REVIEWER = build_component(name="code-reviewer", source="genie")
FORMATTER = build_component(name="formatter", source="skillhub")
AN_AGENT = build_component(ComponentKind.AGENT, name="planner", source="genie")


@pytest.fixture
def no_real_claude_code(monkeypatch):
    report = ToolReport(
        Tool(binary="claude", label="Claude Code"),
        ToolStatus.PRESENT,
        path="/usr/bin/claude",
    )
    monkeypatch.setattr(
        "claude_kit.services.init_service.ensure_tool", lambda tool, install=True: report
    )
    return report


def test_search_gathers_every_source():
    sources = [FakeSource("genie", [REVIEWER]), FakeSource("skillhub", [FORMATTER])]
    found = services.search(ComponentKind.SKILL, "", sources)
    assert [one.name for one in found] == ["code-reviewer", "formatter"]


def test_search_narrows_on_the_query():
    sources = [FakeSource("genie", [REVIEWER, FORMATTER])]
    found = services.search(ComponentKind.SKILL, "format", sources)
    assert [one.name for one in found] == ["formatter"]


def test_search_skips_a_source_that_does_not_serve_the_kind():
    skills_only = FakeSource("skillhub", [FORMATTER], kinds=[ComponentKind.SKILL])
    everything = FakeSource("genie", [AN_AGENT])
    found = services.search(ComponentKind.AGENT, "", [skills_only, everything])
    assert [one.name for one in found] == ["planner"]
    assert skills_only.searched == []


def test_search_still_propagates_an_unreachable_source_today():

    dead = FakeSource("genie", failure=SourceUnreachable("genie", "no network"))
    alive = FakeSource("skillhub", [FORMATTER])
    with pytest.raises(SourceUnreachable):
        services.search(ComponentKind.SKILL, "", [dead, alive])


def test_install_takes_the_first_source_that_has_it():
    genie = FakeSource("genie", [REVIEWER])
    skillhub = FakeSource("skillhub", [REVIEWER])
    installed = services.install(ComponentKind.SKILL, "code-reviewer", [genie, skillhub])
    assert [one.source for one in installed] == ["genie"]
    assert skillhub.installed == []


def test_install_falls_through_to_the_next_source():
    genie = FakeSource("genie", [])
    skillhub = FakeSource("skillhub", [FORMATTER])
    installed = services.install(ComponentKind.SKILL, "formatter", [genie, skillhub])
    assert [one.source for one in installed] == ["skillhub"]
    assert genie.installed == [(ComponentKind.SKILL, "formatter")]


def test_install_answers_empty_when_no_source_has_it():
    sources = [FakeSource("genie", []), FakeSource("skillhub", [])]
    assert services.install(ComponentKind.SKILL, "ghost", sources) == []


def test_uninstall_asks_only_the_named_source():
    genie = FakeSource("genie", [REVIEWER])
    skillhub = FakeSource("skillhub", [REVIEWER])
    asked = ClaudeComponent(
        kind=ComponentKind.SKILL, name="code-reviewer", source="skillhub"
    )
    removed = services.uninstall(asked, [genie, skillhub])
    assert [one.source for one in removed] == ["skillhub"]
    assert genie.uninstalled == []


def test_uninstall_without_a_source_walks_precedence():
    genie = FakeSource("genie", [])
    skillhub = FakeSource("skillhub", [REVIEWER])
    asked = ClaudeComponent(kind=ComponentKind.SKILL, name="code-reviewer", source="")
    removed = services.uninstall(asked, [genie, skillhub])
    assert [one.source for one in removed] == ["skillhub"]


def test_uninstall_from_an_unknown_source_is_a_usage_error():
    asked = ClaudeComponent(
        kind=ComponentKind.SKILL, name="code-reviewer", source="nowhere"
    )
    with pytest.raises(UsageError) as raised:
        services.uninstall(asked, [FakeSource("genie", [REVIEWER])])
    assert raised.value.exit_code is ExitCode.USAGE


def test_listing_without_a_kit_says_to_run_init(tmp_path):
    with pytest.raises(KitNotFound) as raised:
        services.get_installed_components(home=tmp_path / "absent")
    assert "ck init" in str(raised.value)
    assert raised.value.exit_code is ExitCode.NOT_FOUND


def test_status_without_a_kit_says_to_run_init(tmp_path):
    with pytest.raises(KitNotFound):
        services.get_state(home=tmp_path / "absent")


def test_status_reads_back_what_was_cached(kit_home):
    write_state(
        kit_home / STATE_FILE_NAME,
        KitState(message="behind", versions={"ck": VersionStatus(installed="0.1.0")}),
    )
    state = services.get_state(home=kit_home)
    assert state.message == "behind"
    assert state.versions["ck"].installed == "0.1.0"


def test_init_lays_out_the_home(tmp_path, no_real_claude_code):
    home = tmp_path / "kit"
    result = services.init(home=home)
    assert result.created_home is True
    assert result.created_state is True
    assert (home / DATABASE_FILE_NAME).exists()
    assert (home / STATE_FILE_NAME).exists()
    assert result.ok is True


def test_init_twice_leaves_the_same_state(tmp_path, no_real_claude_code):
    home = tmp_path / "kit"
    services.init(home=home)
    again = services.init(home=home)
    assert again.created_home is False
    assert again.created_state is False


def test_init_gives_the_database_its_schema(tmp_path, no_real_claude_code):
    home = tmp_path / "kit"
    services.init(home=home)
    assert services.get_installed_components(home=home) == []


def test_a_skipped_install_is_not_a_failed_one(tmp_path, monkeypatch):
    missing = ToolReport(
        Tool(binary="claude", label="Claude Code"),
        ToolStatus.MISSING,
        error="claude is not on PATH",
    )
    monkeypatch.setattr(
        "claude_kit.services.init_service.ensure_tool",
        lambda tool, install=True: missing,
    )
    result = services.init(home=tmp_path / "kit", install_missing=False)
    assert result.claude_code.ok is False
    assert result.ok is True


def test_a_failed_install_fails_init(tmp_path, monkeypatch):
    missing = ToolReport(
        Tool(binary="claude", label="Claude Code"),
        ToolStatus.MISSING,
        error="npm left claude absent",
    )
    monkeypatch.setattr(
        "claude_kit.services.init_service.ensure_tool",
        lambda tool, install=True: missing,
    )
    result = services.init(home=tmp_path / "kit", install_missing=True)
    assert result.ok is False


def test_the_default_home_is_the_one_the_readme_documents():
    assert CLAUDE_KIT_HOME.name == ".claude-kit"
