"""Content-handler installer (FR-033/FR-041): copies/deletes a component's
declared files for skills/agents. Performs real filesystem I/O — installers/
modules may do I/O, they just never print, prompt, or exit (Principle I).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from src.core.diffing import content_hash
from src.core.state_model import CategoryName, Component, ContentEntry


class ContentInstallError(Exception):
    """Raised when copying a content-handler component's declared files fails."""


def relative_dest(file_path: str) -> Path:
    """Registry file paths are declared as "<category>/<name>/...";
    strip the leading category segment since `target_dir` already *is*
    that category's directory (e.g. ~/.claude/skills/)."""
    parts = Path(file_path).parts
    return Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])


def install_content(
    category: CategoryName,
    name: str,
    component: Component,
    catalog_repo_dir: Path,
    target_dir: Path,
    source: str = "claude-kit",
) -> ContentEntry:
    """Copy every file the component declares from the Catalog Repo into
    `target_dir`. Idempotent: re-running overwrites in place, never
    duplicates."""
    if not component.files:
        raise ContentInstallError(f"{category}.{name} declares no files to install")

    for file in component.files:
        src_path = catalog_repo_dir / file.path
        if not src_path.exists():
            raise ContentInstallError(f"{category}.{name}: source file not found: {src_path}")
        dest_path = target_dir / relative_dest(file.path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)

    return ContentEntry(
        source=source,
        installed_hash=content_hash(component),
        installed_at=datetime.now(UTC),
    )


def remove_content(component: Component, target_dir: Path) -> None:
    """Delete exactly the files this component's install copied, then prune
    any now-empty parent directories back up to (not including) `target_dir`.
    Idempotent: a no-op if already removed."""
    for file in component.files:
        dest_path = target_dir / relative_dest(file.path)
        dest_path.unlink(missing_ok=True)

        parent = dest_path.parent
        while parent != target_dir and target_dir in parent.parents and parent.exists():
            if any(parent.iterdir()):
                break
            parent.rmdir()
            parent = parent.parent
