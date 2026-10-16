"""``ck recommend``: put the newest recommendation skill in place, whether or not it was there."""

from pathlib import Path

from claude_kit import storage
from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import RECOMMEND_SKILL_NAME, UsageError
from claude_kit.services.install_service import install
from claude_kit.services.uninstall_service import uninstall
from claude_kit.sources import Source

__all__ = ["recommend"]


def recommend(
    skill_name: str = RECOMMEND_SKILL_NAME,
    sources: list[Source] | None = None,
    home: Path | None = None,
) -> list[ClaudeComponent]:
    if not skill_name:
        raise UsageError("no recommendation skill is configured yet")

    connection = storage.open_kit_database(home)
    try:
        recorded = storage.find_components_by_name(
            connection, ComponentKind.SKILL, skill_name
        )
    finally:
        connection.close()

    for entry in recorded:
        uninstall(entry.component, sources, home)
    return install(ComponentKind.SKILL, skill_name, sources, home, force=True)
