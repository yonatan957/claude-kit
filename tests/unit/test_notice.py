"""Unit tests for src/core/notice.py's pure findings -> message rendering,
including producing a null message when nothing is new beyond `announced`."""

from src.core.notice import render_notice
from src.core.state_model import Findings


def test_no_findings_produces_null_message():
    findings = Findings(local_cli_version="0.1.0", latest_cli_version="0.1.0")

    message, announced = render_notice(findings, announced=[])

    assert message is None
    assert announced == []


def test_new_cli_version_finding_is_rendered():
    findings = Findings(local_cli_version="0.1.0", latest_cli_version="0.2.0")

    message, announced = render_notice(findings, announced=[])

    assert message is not None
    assert "0.2.0" in message
    assert "cli:0.2.0" in announced


def test_already_announced_finding_is_not_shown_again():
    findings = Findings(local_cli_version="0.1.0", latest_cli_version="0.2.0")

    message, announced = render_notice(findings, announced=["cli:0.2.0"])

    assert message is None
    assert announced == ["cli:0.2.0"]


def test_genuinely_new_finding_after_prior_announcement_is_shown():
    findings = Findings(
        local_cli_version="0.1.0",
        latest_cli_version="0.2.0",
        local_commit="abc",
        remote_commit="def",
    )

    message, announced = render_notice(findings, announced=["cli:0.2.0"])

    assert message is not None
    assert "0.2.0" not in message  # already announced, not repeated
    assert "newer catalog" in message.lower()
    assert set(announced) == {"cli:0.2.0", "catalog:def"}


def test_pending_config_count_is_rendered():
    findings = Findings(
        local_cli_version="0.1.0", latest_cli_version="0.1.0", pending_config_count=2
    )

    message, announced = render_notice(findings, announced=[])

    assert message is not None
    assert "2" in message
    assert "pending:2" in announced


def test_multiple_new_findings_combined_into_one_message():
    findings = Findings(
        local_cli_version="0.1.0",
        latest_cli_version="0.2.0",
        local_commit="abc",
        remote_commit="def",
        pending_config_count=1,
    )

    message, announced = render_notice(findings, announced=[])

    assert message.count("claude-kit:") == 1  # a single pre-rendered notice, not three
    assert len(announced) == 3
