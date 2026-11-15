"""``sync_repo`` against a real git repo in tmp_path, cloned by its path."""

import subprocess
from pathlib import Path

import pytest

from claude_kit.helpers import SourceError, SourceUnreachable, run
from claude_kit.sources import GenieSource
from claude_kit.sources.genie import genie_source
from claude_kit.sources.genie.repo import sync_repo

MANIFEST_TEXT = (Path(__file__).parent / "data" / "genie" / "manifest.json").read_text()
JIRA = '{"kind": "mcp", "name": "jira", "version": "0.1.0", "mcp": {"type": "http"}},'


def commit(repo: Path, manifest_text: str) -> None:
    (repo / "manifest.json").write_text(manifest_text, encoding="utf-8")
    for command in (["add", "."], ["commit", "--quiet", "-m", "update"]):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *command],
            cwd=repo,
            check=True,
        )


@pytest.fixture
def remote(tmp_path) -> Path:
    repo = tmp_path / "remote"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    commit(repo, MANIFEST_TEXT)
    return repo


def test_the_first_sync_clones_the_repo(tmp_path, remote):
    genie_dir = tmp_path / "kit" / "genie"
    manifest = sync_repo(str(remote), genie_dir, run)
    assert [entry.name for entry in manifest.entries] == ["gitlab", "k8s", "kubectl"]
    assert (genie_dir / ".git").is_dir()
    assert (genie_dir / "manifest.json").read_text() == MANIFEST_TEXT


def test_a_broken_manifest_on_the_first_clone_leaves_nothing(tmp_path, remote):
    commit(remote, '{"manifest_version": 1, "entries": [{"kind": "mcp"}]}')
    genie_dir = tmp_path / "kit" / "genie"
    with pytest.raises(SourceError):
        sync_repo(str(remote), genie_dir, run)
    assert not genie_dir.exists()


def test_an_update_shows_the_new_entry(tmp_path, remote):
    genie_dir = tmp_path / "kit" / "genie"
    sync_repo(str(remote), genie_dir, run)
    commit(remote, MANIFEST_TEXT.replace('"entries": [', f'"entries": [{JIRA}'))

    manifest = sync_repo(str(remote), genie_dir, run)
    assert "jira" in [entry.name for entry in manifest.entries]
    assert '"jira"' in (genie_dir / "manifest.json").read_text()


def test_a_broken_manifest_in_the_new_commit_leaves_the_old_copy(tmp_path, remote):
    genie_dir = tmp_path / "kit" / "genie"
    sync_repo(str(remote), genie_dir, run)
    commit(remote, '{"manifest_version": 1, "entries": [{"kind": "mcp"}]}')

    with pytest.raises(SourceError) as raised:
        sync_repo(str(remote), genie_dir, run)
    assert not isinstance(raised.value, SourceUnreachable)
    assert (genie_dir / "manifest.json").read_text() == MANIFEST_TEXT


def test_a_bad_url_is_a_warning(tmp_path):
    source = GenieSource(repo_url=str(tmp_path / "no-such-repo"))
    report = source.init(tmp_path / "kit", True)
    assert report.mark == "!"
    assert report.detail.startswith("unreachable -- git: ")
    assert report.detail.endswith("no local copy")


@pytest.fixture
def claude_md(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "claude" / "CLAUDE.md"
    monkeypatch.setattr(genie_source, "CLAUDE_GLOBAL_MD", path)
    return path


def init_genie(remote: Path, tmp_path: Path) -> str:
    return GenieSource(repo_url=str(remote)).init(tmp_path / "kit", True).detail


def import_line(tmp_path: Path) -> str:
    return f"@{(tmp_path / 'kit' / 'genie' / 'genie.md').as_posix()}"


def test_without_genie_md_claude_md_is_left_alone(tmp_path, remote, claude_md):
    assert init_genie(remote, tmp_path) == f"3 entries from {remote}"
    assert not claude_md.exists()


def commit_genie_md(remote: Path) -> None:
    (remote / "genie.md").write_text("# team rules\n")
    commit(remote, MANIFEST_TEXT)


def test_genie_md_gets_its_import_line(tmp_path, remote, claude_md):
    commit_genie_md(remote)
    assert init_genie(remote, tmp_path) == f"3 entries, genie.md linked from {remote}"
    assert claude_md.read_text() == f"{import_line(tmp_path)}\n"


def test_a_second_init_does_not_add_the_line_again(tmp_path, remote, claude_md):
    commit_genie_md(remote)
    init_genie(remote, tmp_path)
    init_genie(remote, tmp_path)
    assert claude_md.read_text() == f"{import_line(tmp_path)}\n"


def test_a_personal_claude_md_keeps_its_content(tmp_path, remote, claude_md):
    commit_genie_md(remote)
    claude_md.parent.mkdir()
    claude_md.write_text("# mine\n\n- keep this", encoding="utf-8")
    init_genie(remote, tmp_path)
    expected = f"# mine\n\n- keep this\n{import_line(tmp_path)}\n"
    assert claude_md.read_text() == expected
