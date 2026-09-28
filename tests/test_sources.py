"""``SkillHubSource``: the kind filter, the mapping, and which failures are answers."""

import pytest
from fakes import (
    FakeSkillHubClient,
    install_payload,
    search_payload,
    skill_payload,
    uninstall_payload,
)

from claude_kit.components import ComponentKind
from claude_kit.helpers import ExitCode, SourceError, SourceUnreachable, UsageError
from claude_kit.sources import (
    AVAILABLE_SOURCES,
    SkillHubSource,
    find_source_by_name,
    get_source,
    get_source_names,
)
from skillhub_library.errors import CLINotFoundError, CLITimeoutError, CommandError

NOT_THE_SKILL_KINDS = [
    ComponentKind.AGENT,
    ComponentKind.MCP,
    ComponentKind.TOOL,
    ComponentKind.PLUGIN,
]


def build_source(client: FakeSkillHubClient) -> SkillHubSource:
    return SkillHubSource(client=client)


def test_skillhub_serves_only_skills():
    source = build_source(FakeSkillHubClient())
    assert source.kinds == frozenset({ComponentKind.SKILL})
    assert source.supports(ComponentKind.SKILL)


@pytest.mark.parametrize("kind", NOT_THE_SKILL_KINDS)
def test_an_unserved_kind_answers_empty_without_asking_the_cli(kind):
    client = FakeSkillHubClient()
    source = build_source(client)
    assert source.search(kind) == []
    assert source.install(kind, "code-reviewer") == []
    assert source.uninstall(kind, "code-reviewer") == []
    assert client.calls == []


def test_search_maps_a_skill_onto_a_component():
    client = FakeSkillHubClient(search=search_payload(skill_payload()))
    found = build_source(client).search(ComponentKind.SKILL, "review")
    assert len(found) == 1
    component = found[0]
    assert component.kind is ComponentKind.SKILL
    assert component.name == "code-reviewer"
    assert component.source == "skillhub"
    assert component.description == "Reviews code carefully"
    assert component.version == "1.2.0"
    assert component.tag == "global"


def test_search_answers_empty_when_nothing_is_published():
    client = FakeSkillHubClient(search=search_payload())
    assert build_source(client).search(ComponentKind.SKILL) == []


@pytest.mark.parametrize(
    "failure",
    [
        CommandError("search", message="skill not found"),
        CommandError("search", message="NotFound"),
        CommandError("search", message="failed", details={"error": "notFound"}),
    ],
)
def test_a_missing_skill_is_an_answer_not_a_failure(failure):
    client = FakeSkillHubClient(search=failure, install=failure, uninstall=failure)
    source = build_source(client)
    assert source.search(ComponentKind.SKILL, "ghost") == []
    assert source.install(ComponentKind.SKILL, "ghost") == []
    assert source.uninstall(ComponentKind.SKILL, "ghost") == []


def test_an_underscored_error_code_is_not_recognised_as_missing():
    """``_MISSING_WORDS`` matches ``"notFound"`` but not ``"NOT_FOUND"`` -- the
    underscore falls between the two words. Widen the tuple if the registry ever
    answers in that style, and this becomes a missing-skill case instead."""
    failure = CommandError("search", message="failed", details={"code": "NOT_FOUND"})
    with pytest.raises(SourceError):
        build_source(FakeSkillHubClient(search=failure)).search(ComponentKind.SKILL)


def test_any_other_command_failure_is_a_source_error():
    failure = CommandError("search", message="registry rejected the token")
    client = FakeSkillHubClient(search=failure)
    with pytest.raises(SourceError) as raised:
        build_source(client).search(ComponentKind.SKILL)
    assert raised.value.source == "skillhub"
    assert raised.value.exit_code is ExitCode.FAILURE
    assert "skillhub:" in str(raised.value)


@pytest.mark.parametrize(
    "failure",
    [CLINotFoundError("no skillhub on PATH"), CLITimeoutError("timed out after 120s")],
)
def test_a_cli_that_cannot_be_asked_is_unreachable(failure):
    client = FakeSkillHubClient(search=failure)
    with pytest.raises(SourceUnreachable) as raised:
        build_source(client).search(ComponentKind.SKILL)
    assert raised.value.exit_code is ExitCode.UNREACHABLE


def test_install_reports_the_slug_and_namespace_it_used():
    client = FakeSkillHubClient(install=install_payload(namespace="acme"))
    installed = build_source(client).install(ComponentKind.SKILL, "code-reviewer")
    assert [(one.name, one.tag) for one in installed] == [("code-reviewer", "acme")]


def test_uninstall_reports_every_target_it_cleared():
    client = FakeSkillHubClient(
        uninstall=uninstall_payload(
            {"agent": "claude-code", "dir": "a", "namespace": "global"},
            {"agent": "codex", "dir": "b", "namespace": "acme"},
        )
    )
    removed = build_source(client).uninstall(ComponentKind.SKILL, "code-reviewer")
    assert [one.tag for one in removed] == ["global", "acme"]


def test_a_target_that_was_not_there_is_not_reported_as_removed():
    client = FakeSkillHubClient(
        uninstall=uninstall_payload(
            {"agent": "claude-code", "dir": "a", "namespace": "global", "existed": True},
            {"agent": "codex", "dir": "b", "namespace": "acme", "existed": False},
        )
    )
    removed = build_source(client).uninstall(ComponentKind.SKILL, "code-reviewer")
    assert [one.tag for one in removed] == ["global"]


def test_the_registered_sources_are_named_in_precedence_order():
    assert get_source_names() == [source.name for source in AVAILABLE_SOURCES]


def test_find_source_by_name_answers_none_for_a_stranger():
    assert find_source_by_name("nowhere") is None


def test_get_source_names_the_ones_there_are():
    with pytest.raises(UsageError) as raised:
        get_source("nowhere")
    assert "nowhere" in str(raised.value)
    assert "skillhub" in str(raised.value)
    assert raised.value.exit_code is ExitCode.USAGE
