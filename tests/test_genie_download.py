"""``download_manifest``: what lands in the genie folder, and what leaves it alone."""

import io
import urllib.error
from pathlib import Path

import pytest

from claude_kit.helpers import SourceError, SourceUnreachable
from claude_kit.sources.genie import download
from claude_kit.sources.genie.download import download_manifest

MANIFEST_BYTES = (
    Path(__file__).parent / "data" / "genie" / "manifest.json"
).read_bytes()
GITLAB_URL = "https://gitlab.internal/team/genie/-/raw/main/manifest.json"
SCRIPTS = [
    f"scripts/{tool}/{step}.{suffix}"
    for tool in ("k8s", "kubectl")
    for step in ("install", "uninstall")
    for suffix in ("ps1", "sh")
]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


@pytest.fixture
def served(monkeypatch) -> dict[str, bytes]:
    pages: dict[str, bytes] = {}

    def urlopen(url, timeout):
        if url not in pages:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return FakeResponse(pages[url])

    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    return pages


def serve_genie(pages: dict[str, bytes], manifest_url: str) -> None:
    pages[manifest_url] = MANIFEST_BYTES
    base = manifest_url.rsplit("/", 1)[0]
    for script in SCRIPTS:
        pages[f"{base}/{script}"] = f"echo {script}\n".encode()


@pytest.mark.parametrize(
    "manifest_url", [GITLAB_URL, "http://127.0.0.1:8000/manifest.json"]
)
def test_the_manifest_and_every_script_land_in_the_genie_folder(
    tmp_path, served, manifest_url
):
    serve_genie(served, manifest_url)
    genie_dir = tmp_path / "genie"

    manifest = download_manifest(manifest_url, genie_dir)

    assert len(manifest.entries) == 3
    assert (genie_dir / "manifest.json").read_bytes() == MANIFEST_BYTES
    for script in SCRIPTS:
        assert (genie_dir / script).read_text() == f"echo {script}\n"
    assert [path.name for path in tmp_path.iterdir()] == ["genie"]


def test_a_page_that_is_not_json_is_rejected_and_nothing_is_written(tmp_path, served):
    served[GITLAB_URL] = b"<html>Sign in to GitLab</html>"
    with pytest.raises(SourceError) as raised:
        download_manifest(GITLAB_URL, tmp_path / "genie")
    assert "did not return JSON -- is the GitLab project public?" in str(raised.value)
    assert not isinstance(raised.value, SourceUnreachable)
    assert list(tmp_path.iterdir()) == []


def test_an_unreachable_manifest_is_named_with_only_the_reason(tmp_path, monkeypatch):
    def urlopen(url, timeout):
        raise urllib.error.URLError(ConnectionRefusedError("connection refused"))

    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    with pytest.raises(SourceUnreachable) as raised:
        download_manifest(GITLAB_URL, tmp_path / "genie")
    assert str(raised.value) == f"genie: cannot fetch {GITLAB_URL}: connection refused"


@pytest.mark.parametrize(
    "manifest_url",
    [
        "http://gitlab.internal/manifest.json",
        "ftp://gitlab.internal/m.json",
        "file:///m.json",
    ],
)
def test_any_other_scheme_is_refused_before_anything_is_fetched(
    tmp_path, served, manifest_url
):
    with pytest.raises(SourceError) as raised:
        download_manifest(manifest_url, tmp_path / "genie")
    assert not isinstance(raised.value, SourceUnreachable)


def test_a_failed_script_download_leaves_the_previous_copy_intact(tmp_path, served):
    serve_genie(served, GITLAB_URL)
    genie_dir = tmp_path / "genie"
    download_manifest(GITLAB_URL, genie_dir)

    served[GITLAB_URL] = MANIFEST_BYTES.replace(b'"1.2.0"', b'"1.3.0"')
    del served[GITLAB_URL.rsplit("/", 1)[0] + "/scripts/kubectl/uninstall.sh"]
    with pytest.raises(SourceUnreachable):
        download_manifest(GITLAB_URL, genie_dir)

    assert (genie_dir / "manifest.json").read_bytes() == MANIFEST_BYTES
    assert [path.name for path in tmp_path.iterdir()] == ["genie"]
