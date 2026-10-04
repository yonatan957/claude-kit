import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from claude_kit.components import ClaudeComponent, ComponentKind, InstalledComponent
from claude_kit.components.installed_component import ComponentConfig
from claude_kit.helpers import DATABASE_FILE_NAME
from claude_kit.storage import connect, ensure_schema

INSTALLED_AT = "2026-09-01T12:00:00+00:00"


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    connection = connect(":memory:")
    ensure_schema(connection)
    yield connection
    connection.close()


@pytest.fixture
def kit_home(tmp_path: Path) -> Path:
    home = tmp_path / ".claude-kit"
    connection = connect(home / DATABASE_FILE_NAME)
    ensure_schema(connection)
    connection.close()
    return home


def build_component(
    kind: ComponentKind = ComponentKind.SKILL,
    name: str = "code-reviewer",
    source: str = "genie",
    tag: str = "",
    version: str = "",
    description: str = "",
    popularity: int | None = None,
) -> ClaudeComponent:
    return ClaudeComponent(
        kind=kind,
        name=name,
        source=source,
        tag=tag,
        version=version,
        description=description,
        popularity=popularity,
    )


def build_installed(
    component: ClaudeComponent,
    installed_at: str = INSTALLED_AT,
    config: ComponentConfig = ComponentConfig(),
) -> InstalledComponent:
    return InstalledComponent(
        component=component, installed_at=installed_at, config=config
    )
