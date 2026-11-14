"""Copying the genie manifest and its scripts into the kit home. Only ``ck init`` does."""

import http.client
import json
import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from claude_kit.helpers import (
    GENIE_LABEL,
    GENIE_MANIFEST_FILE_NAME,
    TIMEOUT,
    SourceError,
    SourceUnreachable,
)
from claude_kit.sources.genie.manifest import Manifest, parse_manifest

__all__ = ["download_manifest"]

_LOCAL_HOSTS = ("localhost", "127.0.0.1")


def download_manifest(manifest_url: str, genie_dir: Path) -> Manifest:
    """Replace ``genie_dir`` with a fresh copy, or leave it untouched if anything fails."""
    manifest_bytes = _download(manifest_url)
    try:
        manifest_json = json.loads(manifest_bytes)
    except ValueError:
        raise SourceError(
            GENIE_LABEL,
            f"{manifest_url} did not return JSON -- is the GitLab project public?",
        ) from None
    manifest = parse_manifest(manifest_json, manifest_url, genie_dir)
    script_paths = {
        script
        for entry in manifest.entries
        for scripts in (entry.install_scripts, entry.uninstall_scripts)
        for script in scripts.values()
    }

    genie_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=".genie-", dir=genie_dir.parent))
    old_dir = genie_dir.with_name(f".{genie_dir.name}-old")
    try:
        (staging_dir / GENIE_MANIFEST_FILE_NAME).write_bytes(manifest_bytes)
        for script in script_paths:
            target = staging_dir / script
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_download(urllib.parse.urljoin(manifest_url, script)))
        shutil.rmtree(old_dir, ignore_errors=True)
        if genie_dir.exists():
            genie_dir.rename(old_dir)
        staging_dir.rename(genie_dir)
        shutil.rmtree(old_dir, ignore_errors=True)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
    return manifest


def _download(url: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    is_local_http = parts.scheme == "http" and parts.hostname in _LOCAL_HOSTS
    if parts.scheme != "https" and not is_local_http:
        raise SourceError(
            GENIE_LABEL, f"{url}: only https:// (or http:// on localhost) is allowed"
        )
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except (OSError, http.client.HTTPException) as failure:
        reason = getattr(failure, "reason", failure)
        raise SourceUnreachable(
            GENIE_LABEL, f"cannot fetch {url}: {reason}"
        ) from failure
