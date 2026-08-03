"""Integration test: `claude-kit init` verifies the environment, creates
dirs/baseline files, deploys genie-claude.md, and appends the CLAUDE.md
reference line exactly once — re-running `init` adds no duplicate
(FR-001-FR-005)."""

import pytest
import typer

from src.commands import config_cmd, init_cmd


@pytest.fixture
def fake_claude_env(tmp_path, monkeypatch):
    """A tmp_path-based fake `~` with a pre-existing `.claude/` (i.e. Claude
    Code has already been run once), and init_cmd's already-bound path
    functions redirected into it."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_kit_dir = tmp_path / ".claude-kit"
    claude_kit_repo_dir = tmp_path / ".claude-kit-repo"
    claude_md_path = claude_dir / "CLAUDE.md"
    env_dir = claude_kit_dir / "env.d"

    monkeypatch.setattr(init_cmd, "claude_dir", lambda: claude_dir)
    monkeypatch.setattr(init_cmd, "claude_kit_dir", lambda: claude_kit_dir)
    monkeypatch.setattr(init_cmd, "claude_kit_repo_dir", lambda: claude_kit_repo_dir)
    monkeypatch.setattr(init_cmd, "claude_md_path", lambda: claude_md_path)
    monkeypatch.setattr(init_cmd, "env_dir", lambda: env_dir)

    # Isolate from the real interactive config flow (a separate concern,
    # covered by tests/integration/test_story1_picker.py and friends).
    calls = []
    monkeypatch.setattr(config_cmd, "run_config", lambda category=None: calls.append(category))

    return {
        "claude_dir": claude_dir,
        "claude_kit_dir": claude_kit_dir,
        "claude_kit_repo_dir": claude_kit_repo_dir,
        "claude_md_path": claude_md_path,
        "env_dir": env_dir,
        "config_calls": calls,
    }


def test_init_refuses_with_no_claude_code_environment(tmp_path, monkeypatch):
    missing_claude_dir = tmp_path / ".claude"  # never created

    monkeypatch.setattr(init_cmd, "claude_dir", lambda: missing_claude_dir)

    with pytest.raises(typer.Exit) as exc_info:
        init_cmd.run_init()

    assert exc_info.value.exit_code == 1
    assert not missing_claude_dir.exists()


def test_init_creates_directories_and_baseline_files(fake_claude_env):
    init_cmd.run_init()

    assert fake_claude_env["claude_kit_dir"].is_dir()
    assert fake_claude_env["claude_kit_repo_dir"].is_dir()
    assert fake_claude_env["env_dir"].is_dir()
    assert (fake_claude_env["claude_dir"] / "genie-claude.md").exists()


def test_init_appends_claude_md_reference_line_exactly_once(fake_claude_env):
    fake_claude_env["claude_md_path"].write_text("# My existing notes\n\nDo not touch this.\n")

    init_cmd.run_init()

    content = fake_claude_env["claude_md_path"].read_text()
    assert "Do not touch this." in content
    assert content.count(init_cmd.CLAUDE_MD_REFERENCE_LINE) == 1


def test_init_run_twice_adds_no_duplicate_reference_line(fake_claude_env):
    init_cmd.run_init()
    init_cmd.run_init()

    content = fake_claude_env["claude_md_path"].read_text()
    assert content.count(init_cmd.CLAUDE_MD_REFERENCE_LINE) == 1


def test_init_transitions_into_config_on_success(fake_claude_env):
    init_cmd.run_init()

    assert fake_claude_env["config_calls"] == [None]
