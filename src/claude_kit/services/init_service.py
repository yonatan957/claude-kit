"""``ck init``: make sure Claude Code is there, then lay out the kit's home."""

from dataclasses import dataclass
from pathlib import Path

from claude_kit.helpers import (
    CLAUDE_BINARY,
    CLAUDE_INSTALL_COMMAND,
    CLAUDE_KIT_HOME,
    CLAUDE_LABEL,
    DATABASE_FILE_NAME,
    STATE_FILE_NAME,
    Tool,
    ToolReport,
    ensure_tool,
)
from claude_kit.storage import KitState, connect, ensure_schema, write_state

__all__ = ["CLAUDE_CODE", "InitResult", "init"]

CLAUDE_CODE = Tool(
    binary=CLAUDE_BINARY, label=CLAUDE_LABEL, install=CLAUDE_INSTALL_COMMAND
)


@dataclass(frozen=True)
class InitResult:
    home: Path
    database: Path
    state: Path
    created_home: bool
    created_state: bool
    claude_code: ToolReport

    @property
    def ok(self) -> bool:
        return self.claude_code.ok


def init(
    home: Path | None = None,
    install_missing: bool = True,
) -> InitResult:
    """Create the home, schema and state file. Existing ones are left alone."""
    home = home or CLAUDE_KIT_HOME
    claude_code = ensure_tool(CLAUDE_CODE, install=install_missing)

    created_home = not home.exists()
    home.mkdir(parents=True, exist_ok=True)

    database = home / DATABASE_FILE_NAME
    connection = connect(database)
    try:
        ensure_schema(connection)
    finally:
        connection.close()

    state = home / STATE_FILE_NAME
    created_state = not state.exists()
    if created_state:
        write_state(state, KitState())

    return InitResult(
        home=home,
        database=database,
        state=state,
        created_home=created_home,
        created_state=created_state,
        claude_code=claude_code,
    )
