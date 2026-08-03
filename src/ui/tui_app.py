"""The inline picker application (FR-045).

`full_screen=False` is the load-bearing detail: prompt_toolkit renders below
the shell prompt in the terminal's normal buffer, never entering the alternate
screen, so the developer's scrollback survives untouched and the final frame
stays in history like ordinary command output.

This is the only module permitted to import `Application`.
"""

from __future__ import annotations

from prompt_toolkit.application import Application
from prompt_toolkit.layout import FormattedTextControl, Layout, Window
from prompt_toolkit.layout.dimension import Dimension

from src.core.state_model import CategoryName, InstalledRecord, Registry
from src.ui.entry import PickerEntry
from src.ui.keys import build_key_bindings
from src.ui.render import VIEWPORT_ROWS, render
from src.ui.screens.picker import CATEGORIES
from src.ui.state import PickerState
from src.ui.style import PICKER_STYLE


def build_entries(
    registry: Registry,
    installed: InstalledRecord,
    category_filter: CategoryName | None = None,
    naming_collisions: dict[str, set[str]] | None = None,
) -> list[PickerEntry]:
    collisions = naming_collisions or {}
    by_category = registry.components_by_category()
    categories = (category_filter,) if category_filter else CATEGORIES
    entries: list[PickerEntry] = []
    for category in categories:
        installed_names = set(getattr(installed, category).keys())
        colliding = collisions.get(category, set())
        for name, component in by_category[category].items():
            entries.append(
                PickerEntry(
                    category=category,
                    name=name,
                    component=component,
                    currently_installed=name in installed_names,
                    selected=name in installed_names,
                    naming_collision=name in colliding,
                )
            )
    return entries


def build_application(state: PickerState) -> Application:
    window = Window(
        content=FormattedTextControl(lambda: render(state), focusable=True),
        height=Dimension(min=1, max=VIEWPORT_ROWS + 2),
        wrap_lines=False,
    )
    return Application(
        layout=Layout(window),
        key_bindings=build_key_bindings(state),
        style=PICKER_STYLE,
        full_screen=False,
        erase_when_done=False,
    )


def run_picker(
    registry: Registry,
    installed: InstalledRecord,
    category_filter: CategoryName | None = None,
    naming_collisions: dict[str, set[str]] | None = None,
) -> dict[str, set[str]] | None:
    """Returns the desired selection, or `None` if cancelled (FR-008)."""
    entries = build_entries(registry, installed, category_filter, naming_collisions)
    state = PickerState(entries, category_filter)
    return build_application(state).run()
