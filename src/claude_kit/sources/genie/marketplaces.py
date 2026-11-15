"""Which plugin marketplaces the team uses: ``marketplaces.json`` in the genie repo."""

import json
import logging
from pathlib import Path

from claude_kit.helpers import CLAUDE_KIT_HOME, GENIE_DIR_NAME, MARKETPLACES_FILE_NAME

__all__ = ["read_marketplaces"]

_log = logging.getLogger(__name__)


def read_marketplaces(
    genie_dir: Path = CLAUDE_KIT_HOME / GENIE_DIR_NAME,
) -> dict[str, str]:
    """``{name: git url}``. Missing or broken answers empty: every command reads this
    at startup, and a bad list must cost only the marketplaces, not the whole kit."""
    path = genie_dir / MARKETPLACES_FILE_NAME
    if not path.is_file():
        return {}
    try:
        marketplaces: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as failure:
        _log.warning("genie: %s is not JSON (%s) -- no marketplaces", path, failure)
        return {}
    return marketplaces
