"""``ck init``: make sure Claude Code and SkillHub are there, then lay out the kit's home."""

from dataclasses import dataclass
from pathlib import Path

from claude_kit.helpers import (
    CLAUDE_BINARY,
    CLAUDE_INSTALL_COMMAND,
    CLAUDE_KIT_HOME,
    CLAUDE_LABEL,
    DATABASE_FILE_NAME,
    SKILLHUB_LABEL,
    STATE_FILE_NAME,
    Tool,
    ToolReport,
    ensure_tool,
)
from claude_kit.storage import KitState, connect, ensure_schema, write_state
from skillhub_library.consts import BINARIES as SKILLHUB_BINARIES
from skillhub_library.consts import INSTALL_COMMAND as SKILLHUB_INSTALL_COMMAND

__all__ = ["CLAUDE_CODE", "SKILLHUB", "InitResult", "init"]

CLAUDE_CODE = Tool(
    binary=CLAUDE_BINARY, label=CLAUDE_LABEL, install=CLAUDE_INSTALL_COMMAND
)
SKILLHUB = Tool(
    binary=SKILLHUB_BINARIES[0], label=SKILLHUB_LABEL, install=SKILLHUB_INSTALL_COMMAND
)


@dataclass(frozen=True)
class InitResult:
    home: Path
    database: Path
    state: Path
    created_home: bool
    created_state: bool
    claude_code: ToolReport
    skillhub: ToolReport
    attempted_install: bool

    @property
    def tools(self) -> tuple[ToolReport, ...]:
        return (self.claude_code, self.skillhub)

    @property
    def tools_ok(self) -> bool:
        return all(report.ok for report in self.tools)

    @property
    def ok(self) -> bool:
        """A step the caller asked us to skip is not a step that failed."""
        return self.tools_ok or not self.attempted_install


def init(
    home: Path | None = None,
    install_missing: bool = True,
) -> InitResult:
    """Create the home, schema and state file. Existing ones are left alone."""
    home = home or CLAUDE_KIT_HOME
    claude_code = ensure_tool(CLAUDE_CODE, install=install_missing)
    skillhub = ensure_tool(SKILLHUB, install=install_missing)

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
        skillhub=skillhub,
        attempted_install=install_missing,
    )
