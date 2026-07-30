"""Generic snapshot -> apply -> health-check -> commit-or-revert transaction primitive.

This is the mechanism Constitution Principle I (Test-Before-Mutation, NON-NEGOTIABLE)
requires behind every write to a user-owned file. Each call covers exactly the paths
given to it — a failure here reverts only those paths, so one component's failure can
never undo another, already-committed component's write (FR-014).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any


class TransactionResult:
    def __init__(self, ok: bool, detail: str | None = None):
        self.ok = ok
        self.detail = detail


def atomic_write(path: Path, content: str) -> None:
    """Write via a temp file in the same directory, then atomically swap it in —
    there is never a moment where `path` holds partial content."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _snapshot(paths: list[Path]) -> dict[Path, str | None]:
    return {Path(p): (Path(p).read_text(encoding="utf-8") if Path(p).exists() else None) for p in paths}


def _restore(snapshot: dict[Path, str | None]) -> None:
    for p, content in snapshot.items():
        if content is None:
            if p.exists():
                p.unlink()
        else:
            atomic_write(p, content)


def run_transaction(
    paths: list[Path],
    apply_fn: Callable[[], Any],
    verify_fn: Callable[[Any], bool] | None = None,
) -> TransactionResult:
    """Snapshot `paths`, run `apply_fn`, health-check with `verify_fn`, commit or revert."""
    snapshot = _snapshot(paths)
    try:
        result = apply_fn()
    except Exception as exc:  # noqa: BLE001 - any apply failure must revert
        _restore(snapshot)
        return TransactionResult(ok=False, detail=str(exc))

    if verify_fn is not None:
        try:
            healthy = verify_fn(result)
        except Exception as exc:  # noqa: BLE001
            _restore(snapshot)
            return TransactionResult(ok=False, detail=f"health-check raised: {exc}")
        if not healthy:
            _restore(snapshot)
            return TransactionResult(ok=False, detail="health-check failed")

    return TransactionResult(ok=True, detail=None)
