"""Contract test: Constitution Principle VI — no Python file over 90 lines.

Measurement is **total physical lines** (blanks, comments, and docstrings all
count), per research.md 1b: it is the strictest reading, needs no parser, and
cannot be gamed by reformatting.

`DEFERRED_OVER_LIMIT` holds the files that already exceeded the cap when the
principle was ratified (constitution v1.1.0, 2026-08-03). They are tracked in
plan.md's Complexity Tracking table and split by tasks T099-T101 (Phase 14);
remove each entry as its split lands, then delete the allowlist entirely.
Nothing may ever be *added* to this list.
"""

from __future__ import annotations

from pathlib import Path

MAX_LINES = 90

SRC_DIR = Path(__file__).resolve().parents[2] / "src"

DEFERRED_OVER_LIMIT: frozenset[str] = frozenset(
    {
        "installers/script.py",
        "core/state_model.py",
        "commands/update_cmd.py",
        "installers/settings_patch.py",
        "commands/add_remove_cmd.py",
        "core/diffing.py",
        "commands/check_cmd.py",
        "notify/hook.py",
    }
)


def line_count(path: Path) -> int:
    """Total physical lines, counted the same way `wc -l`-style tools do."""
    return len(path.read_text(encoding="utf-8").splitlines())


def _relative(path: Path) -> str:
    return path.relative_to(SRC_DIR).as_posix()


def test_no_source_file_exceeds_line_limit() -> None:
    offenders = {
        _relative(p): line_count(p)
        for p in sorted(SRC_DIR.rglob("*.py"))
        if line_count(p) > MAX_LINES and _relative(p) not in DEFERRED_OVER_LIMIT
    }

    assert not offenders, (
        "Constitution Principle VI: these files exceed "
        f"{MAX_LINES} total physical lines and must be split into "
        "single-responsibility modules before merge:\n"
        + "\n".join(f"  {name}: {count} lines" for name, count in offenders.items())
    )


def test_deferred_allowlist_has_no_stale_entries() -> None:
    """A split that lands must remove its file from the allowlist.

    Without this, the allowlist silently keeps exempting files that are
    already compliant, and Principle VI quietly stops being enforced for them.
    """
    stale = sorted(
        name
        for name in DEFERRED_OVER_LIMIT
        if not (SRC_DIR / name).exists() or line_count(SRC_DIR / name) <= MAX_LINES
    )

    assert not stale, (
        "These files no longer exceed the limit (or no longer exist) and must "
        "be removed from DEFERRED_OVER_LIMIT:\n" + "\n".join(f"  {n}" for n in stale)
    )
