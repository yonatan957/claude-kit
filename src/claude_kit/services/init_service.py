"""``ck init``: Claude Code, the kit's home, then every source sets itself up."""

from dataclasses import dataclass
from pathlib import Path

from claude_kit.helpers import (
    CLAUDE_BINARY,
    CLAUDE_INSTALL_COMMAND,
    CLAUDE_KIT_HOME,
    CLAUDE_LABEL,
    DATABASE_FILE_NAME,
    STATE_FILE_NAME,
    KitError,
    SourceError,
    Tool,
    ToolReport,
    ensure_tool,
)
from claude_kit.sources import AVAILABLE_SOURCES, InitReport, Source, refresh_sources
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
    attempted_install: bool
    sources: list[InitReport]

    @property
    def ok(self) -> bool:
        """A step the caller asked us to skip is not a step that failed."""
        claude_code_ok = self.claude_code.ok or not self.attempted_install
        return claude_code_ok and all(report.ok for report in self.sources)


def init(
    home: Path | None = None,
    install_missing: bool = True,
    sources: list[Source] | None = None,
) -> InitResult:
    """Create the home, schema and state file. Existing ones are left alone."""
    home = home or CLAUDE_KIT_HOME
    refresh = sources is None
    sources = AVAILABLE_SOURCES if sources is None else sources
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

    reports: list[InitReport] = []
    done: set[str] = set()
    # the list is read again after each init: genie's brings in the marketplaces
    while pending := [source for source in sources if source.name not in done]:
        source = pending[0]
        done.add(source.name)
        try:
            report = source.init(home, install_missing)
        except KitError as failure:
            reason = (
                failure.reason if isinstance(failure, SourceError) else str(failure)
            )
            report = InitReport("✗", source.name, reason)
        if report is not None:
            reports.append(report)
        if refresh:
            refresh_sources()

    return InitResult(
        home=home,
        database=database,
        state=state,
        created_home=created_home,
        created_state=created_state,
        claude_code=claude_code,
        attempted_install=install_missing,
        sources=reports,
    )
