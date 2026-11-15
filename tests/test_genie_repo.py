"""``sync_repo`` against a real git repo in tmp_path, cloned by its path."""

import subprocess
from pathlib import Path

import pytest

from claude_kit.helpers import SourceError, SourceUnreachable, run
from claude_kit.sources import GenieSource
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
