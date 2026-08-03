"""Launch the real picker against the test fixture catalog — nothing is installed.

This exists so FR-045/FR-046/FR-047 can be eyeballed in a real terminal, which
is the one part of T095 no automated test can cover.

    python tools/demo_picker.py

WHAT TO LOOK FOR
----------------
1. INLINE (FR-045). The picker draws *below* your prompt. Everything that was
   on screen before stays visible above it. The screen must not blank out.
2. NO CLUTTER (FR-046). Only three things: the counts line, the list, and one
   line of key hints. No header bar, no footer widget, no theme switcher.
3. TAB (FR-009). Tab enters search; Tab leaves it. That is the only way in and
   the only way out — there is no "exit search" row or button anywhere.
4. ENTER (FR-007). Enter toggles the highlighted row. Watch the marker change.
5. DEAD KEYS (FR-007/FR-012). Press `a`. Press `Space`. Nothing should happen.
6. APPROVE (FR-012). Arrow down to "Approve & Install" at the bottom, press
   Enter. That is the only way to approve.
7. MARKERS (FR-047). [ ] unselected, [v] selected (green), [X] pending removal
   (red). Move the cursor on and off a row — the marker must not change or
   disappear.
8. SCROLLBACK (SC-010). After it exits, scroll up. Everything from before you
   launched it must still be reachable.

Esc or Ctrl-C cancels.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.core.state_model import ContentEntry, InstalledRecord, Registry  # noqa: E402
from src.ui.tui_app import run_picker  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"


def main() -> int:
    registry = Registry.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))

    # Pretend one skill is already installed, so a [X] "pending removal" marker
    # is reachable by deselecting it (check #7 above).
    installed = InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T00:00:00Z",
        catalog_commit="demo",
        registry_version=registry.version,
        cli_version="0.1.0",
    )
    installed.skills["fixture-skill"] = ContentEntry(
        source="claude-kit",
        installed_hash="demo",
        installed_at="2026-08-03T00:00:00Z",
    )

    print("Launching the picker. Read this file's docstring for what to check.\n")
    result = run_picker(registry, installed)

    print()
    if result is None:
        print("Cancelled — no selection returned (FR-008).")
    else:
        chosen = {c: sorted(n) for c, n in result.items() if n}
        print(f"Approved. Desired selection: {chosen or 'nothing selected'}")
    print("Nothing was installed — this is a display-only harness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
