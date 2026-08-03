"""Restricted secret file writer/deleter/reader (research.md #7, FR-016/
FR-039): `chmod 600` on POSIX, an owner-only ACL on Windows. One shared
function per operation so callers never branch on OS.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path


def write_secret_file(path: Path, contents: str) -> None:
    """Write `contents` to `path`, creating parent dirs as needed, and
    restrict the file to owner-only access. Idempotent: overwrites in place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    _restrict_to_owner(path)


def read_secret_file(path: Path) -> str | None:
    """Returns the file's contents, or None if it doesn't exist."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def delete_secret_file(path: Path) -> None:
    """Idempotent: a no-op if the file doesn't exist."""
    path.unlink(missing_ok=True)


def _restrict_to_owner(path: Path) -> None:
    if sys.platform == "win32":
        _restrict_to_owner_windows(path)
    else:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _restrict_to_owner_windows(path: Path) -> None:
    username = os.environ.get("USERNAME")
    if not username:
        return
    subprocess.run(
        ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:F"],
        capture_output=True,
        text=True,
        check=False,
    )
