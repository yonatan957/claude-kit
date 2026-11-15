"""``MarketplaceSource``: one per listed marketplace. It registers its marketplace,
reads the catalog Claude Code cloned, and hands every install to ``claude plugin``."""

import json
from pathlib import Path

import pytest
from fakes import FakeRunner

from claude_kit.components import ComponentKind
from claude_kit.helpers import SourceError
from claude_kit.sources import MarketplaceSource
from claude_kit.sources.genie import read_marketplaces

PLUGIN = ComponentKind.PLUGIN
URL = "https://git/team.git"


def write_json(path: Path, content: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")


def clone(tmp_path: Path, *plugins: dict) -> dict:
    """What Claude Code leaves behind after `claude plugin marketplace add`."""
    location = tmp_path / "marketplaces" / "team"
    write_json(location / ".claude-plugin" / "marketplace.json", {"plugins": plugins})
    return {"team": {"installLocation": str(location)}}


def build_source(tmp_path, known=None, runner=None) -> MarketplaceSource:
    known_file = tmp_path / "known_marketplaces.json"
    write_json(known_file, known or {})
    return MarketplaceSource("team", URL, known_file, runner or FakeRunner())


def test_genie_reads_the_listed_marketplaces(tmp_path):
    write_json(tmp_path / "marketplaces.json", {"team": URL})
    assert read_marketplaces(tmp_path) == {"team": URL}


@pytest.mark.parametrize("content", [None, "{ not json"])
def test_a_missing_or_broken_list_means_no_marketplaces(tmp_path, content):
    if content:
        (tmp_path / "marketplaces.json").write_text(content, encoding="utf-8")
    assert read_marketplaces(tmp_path) == {}


@pytest.mark.parametrize(
    "cloned, expected",
    [(False, ["marketplace", "add", URL]), (True, ["marketplace", "update", "team"])],
)
def test_init_adds_a_new_marketplace_and_updates_a_known_one(
    tmp_path, cloned, expected
):
    runner = FakeRunner()
    known = clone(tmp_path) if cloned else {}
    report = build_source(tmp_path, known, runner).init(tmp_path, True)
    assert report.mark == "✓"
    assert [call.command[2:] for call in runner.calls] == [expected]


def test_init_warns_without_failing_when_it_cannot_sync(tmp_path):
    runner = FakeRunner(failing={"marketplace": "network down"})
    report = build_source(tmp_path, runner=runner).init(tmp_path, True)
    assert report.mark == "!"
    assert "network down" in report.detail


def test_search_reads_the_cloned_catalog(tmp_path):
    known = clone(tmp_path, {"name": "onyx", "description": "Onyx MCPs"}, {"name": "x"})
    found = build_source(tmp_path, known).search(PLUGIN, "mcps")
    assert [(one.name, one.source, one.kind) for one in found] == [
        ("onyx", "team", PLUGIN)
    ]


def test_install_and_uninstall_name_the_marketplace(tmp_path):
    runner = FakeRunner()
    source = build_source(tmp_path, clone(tmp_path, {"name": "onyx"}), runner)
    assert source.install(PLUGIN, "onyx")
    assert source.uninstall(PLUGIN, "onyx")
    assert [call.command[2:] for call in runner.calls] == [
        ["install", "onyx@team"],
        ["uninstall", "onyx@team"],
    ]


def test_what_the_marketplace_does_not_have_answers_empty_and_runs_nothing(tmp_path):
    runner = FakeRunner()
    source = build_source(tmp_path, clone(tmp_path, {"name": "onyx"}), runner)
    assert source.install(PLUGIN, "ghost") == []
    assert source.install(ComponentKind.SKILL, "onyx") == []
    assert build_source(tmp_path, runner=runner).search(PLUGIN) == []
    assert runner.calls == []


def test_a_failed_claude_plugin_call_is_a_source_error(tmp_path):
    runner = FakeRunner(failing={"install": "plugin not found"})
    source = build_source(tmp_path, clone(tmp_path, {"name": "onyx"}), runner)
    with pytest.raises(SourceError, match="plugin not found"):
        source.install(PLUGIN, "onyx")
