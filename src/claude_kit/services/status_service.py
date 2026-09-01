"""``ck status``: the answer the kit cached at its last update check."""

from pathlib import Path

from claude_kit.helpers import CLAUDE_KIT_HOME, STATE_FILE_NAME, KitNotFound
from claude_kit.storage import KitState, read_state

__all__ = ["get_state"]


def get_state(home: Path | None = None) -> KitState:
    home = home or CLAUDE_KIT_HOME
    if not home.exists():
        raise KitNotFound(home)
    return read_state(home / STATE_FILE_NAME)
