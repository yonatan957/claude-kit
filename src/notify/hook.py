"""Session-start notify hook (Principle V — instant boot): a fast, local-only
read of state.json that prints `message` verbatim if present.

Deliberately has ZERO imports from core/, installers/, or anything network/
git-touching — the state.json path and a minimal JSON read are inlined here
rather than importing src/core/paths.py or src/core/state_model.py, so this
module's own import graph stays trivially small and fast (FR-030/FR-031).
"""

from __future__ import annotations

import json
from pathlib import Path


def _state_json_path() -> Path:
    return Path.home() / ".claude-kit" / "state.json"


def print_notice() -> None:
    path = _state_json_path()
    if not path.exists():
        return
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    message = data.get("message")
    if message:
        print(message)
