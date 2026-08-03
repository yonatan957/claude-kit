"""Contract test: Constitution Principle VI — no Python file over 90 lines of code.

Measurement is **lines of code**: physical lines that are neither blank nor
comment-only. Docstrings count; blanks and `#` comments do not (constitution
v1.2.0, which supersedes the earlier total-physical-lines rule — that metric
penalised documentation rather than complexity, and was abandoned after it
caused docstrings to be deleted just to fit).

`DEFERRED_OVER_LIMIT` holds files that predate mechanical enforcement and are
tracked in plan.md's Complexity Tracking table. Remove each entry as its split
lands, then delete the allowlist entirely. Nothing may ever be *added* to it.
"""

from __future__ import annotations

from pathlib import Path

MAX_LINES = 90

SRC_DIR = Path(__file__).resolve().parents[2] / "src"

DEFERRED_OVER_LIMIT: frozenset[str] = frozenset(
    {
        "installers/script.py",
        "commands/update_cmd.py",
    }
)


def line_count(path: Path) -> int:
    """Lines of code: non-blank, non-comment-only physical lines."""
    return sum(
        1
        for raw in path.read_text(encoding="utf-8").splitlines()
        if (line := raw.strip()) and not line.startswith("#")
    )


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
        f"{MAX_LINES} lines of code and must be split into "
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
