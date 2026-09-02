"""``ck status``: the answer the kit cached at its last update check."""

from pathlib import Path

from claude_kit.helpers import CLAUDE_KIT_HOME, STATE_FILE_NAME, KitNotFound
from claude_kit.storage import KitState, read_state

__all__ = ["get_state"]


def get_state(home: Path | None = None) -> KitState:
    """The last check, or ``KitNotFound`` -- an empty answer would read as "nothing
    is behind", which is a different claim from "nothing has been checked"."""
    home = home or CLAUDE_KIT_HOME
    state = home / STATE_FILE_NAME
    if not state.exists():
        raise KitNotFound(home)
    return read_state(state)
