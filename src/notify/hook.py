"""Session-start notify hook (Principle V — instant boot): a fast, local-only
read of state.json that prints `message` verbatim if present.

Deliberately has ZERO imports from core/, installers/, or anything network/
git-touching — the state.json path and a minimal JSON read are inlined here
rather than importing src/core/paths.py or src/core/state_model.py, so this
module's own import graph stays trivially small and fast (FR-030/FR-031).
"""

from __future__ import annotations

import json
import subprocess
import sys
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


def _check_command() -> list[str]:
    return [sys.executable, "-m", "src.cli", "check"]


def launch_detached_check() -> None:
    """Fire-and-forget (research.md #6): launches `claude-kit check` as a
    fully detached child process and returns immediately without waiting on
    it — `subprocess.Popen` itself is not a network/git call, only the
    detached child it starts does that work, off this module's critical path.
    """
    popen_kwargs: dict = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        popen_kwargs["start_new_session"] = True
    subprocess.Popen(_check_command(), **popen_kwargs)  # noqa: S603 - fixed, non-shell argv


def main() -> None:
    print_notice()
    launch_detached_check()


if __name__ == "__main__":
    main()
