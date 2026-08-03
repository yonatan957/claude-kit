"""Textual TUI: two-step picker (FR-006-FR-013) + sequential configure
prompts (FR-014/FR-015).
"""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, ListItem, ListView, Static

from src.core.state_model import CategoryName, Component, ComponentInput, InstalledRecord, Registry

_CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


@dataclass
class PickerEntry:
    category: CategoryName
    name: str
    component: Component
    currently_installed: bool
    selected: bool
    pinned: bool = False
    naming_collision: bool = False  # FR-043: an existing "user"-sourced item shares this name

    @property
    def pending_removal(self) -> bool:
        return self.currently_installed and not self.selected

    @property
    def pending_addition(self) -> bool:
        return not self.currently_installed and self.selected


class PickerApp(App[dict[str, set[str]] | None]):
    """Step 1: the combined picker across every declared category. Returns
    the desired selection (category -> set of names) on approval, or None on
    cancel (FR-008)."""

    CSS = """
    ListView { height: 1fr; }
    #counts { height: auto; padding: 0 1; }
    #search-input { display: none; }
    #search-input.visible { display: block; }
    """

    BINDINGS = [
        Binding("space", "toggle", "Toggle"),
        Binding("/", "toggle_search", "Search"),
        Binding("a", "approve", "Approve & install"),
        Binding("q", "cancel", "Cancel"),
        Binding("escape", "cancel_search_or_quit", "Cancel/Back", show=False),
    ]

    search_mode: reactive[bool] = reactive(False)

    def __init__(
        self,
        registry: Registry,
        installed: InstalledRecord,
        category_filter: CategoryName | None = None,
        naming_collisions: dict[str, set[str]] | None = None,
    ) -> None:
        super().__init__()
        self.registry = registry
        self.installed = installed
        self.category_filter = category_filter
        self.naming_collisions = naming_collisions or {}
        self.entries: list[PickerEntry] = self._build_entries()
        self.cancelled = False

    def _build_entries(self) -> list[PickerEntry]:
        entries: list[PickerEntry] = []
        components_by_category = self.registry.components_by_category()
        categories = (self.category_filter,) if self.category_filter else _CATEGORIES
        for category in categories:
            installed_names = set(getattr(self.installed, category).keys())
            colliding_names = self.naming_collisions.get(category, set())
            for name, component in components_by_category[category].items():
                entries.append(
                    PickerEntry(
                        category=category,
                        name=name,
                        component=component,
                        currently_installed=name in installed_names,
                        selected=name in installed_names,
                        naming_collision=name in colliding_names,
                    )
                )
        return entries

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="counts")
        yield Input(placeholder="Search...", id="search-input")
        yield ListView(id="picker-list")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).can_focus = False
        self._refresh_list()
        self.query_one("#picker-list", ListView).focus()

    def _visible_entries(self) -> list[PickerEntry]:
        if not self.search_mode:
            # Items selected while in search mode float to the top on return
            # to browsing (FR-010).
            pinned = [e for e in self.entries if e.pinned]
            rest = [e for e in self.entries if not e.pinned]
            return pinned + rest
        query = self.query_one("#search-input", Input).value.strip().lower()
        if not query:
            return list(self.entries)
        return [
            e
            for e in self.entries
            if query in e.name.lower() or query in e.component.description.lower()
        ]

    def _label_for(self, entry: PickerEntry) -> str:
        base = f"[{entry.category}] {entry.name} - {entry.component.description}"
        if entry.naming_collision:
            base = f"(!) manually-placed item with this name already exists — {base}"
        if entry.pending_removal:
            return f"(pending removal) {base}"
        mark = "[x]" if entry.selected else "[ ]"
        return f"{mark} {base}"

    def _refresh_list(self) -> None:
        list_view = self.query_one("#picker-list", ListView)
        list_view.clear()
        visible = self._visible_entries()
        for entry in visible:
            item = ListItem(Static(self._label_for(entry)))
            item.entry = entry  # type: ignore[attr-defined]
            list_view.append(item)
        if visible:
            list_view.index = 0
        self._refresh_counts()

    def _refresh_counts(self) -> None:
        counts = self.query_one("#counts", Static)
        parts = [
            f"{category}: {sum(1 for e in self.entries if e.category == category and e.selected)}"
            for category in _CATEGORIES
            if self.category_filter is None or category == self.category_filter
        ]
        counts.update(" | ".join(parts))

    def action_toggle(self) -> None:
        list_view = self.query_one("#picker-list", ListView)
        highlighted = list_view.highlighted_child
        if highlighted is None:
            return
        entry: PickerEntry = highlighted.entry  # type: ignore[attr-defined]
        entry.selected = not entry.selected
        if self.search_mode and entry.selected:
            entry.pinned = True
        self._refresh_list()

    def action_toggle_search(self) -> None:
        self.search_mode = not self.search_mode
        search_input = self.query_one("#search-input", Input)
        search_input.set_class(self.search_mode, "visible")
        search_input.can_focus = self.search_mode
        if self.search_mode:
            search_input.value = ""
            search_input.focus()
        else:
            self.query_one("#picker-list", ListView).focus()
        self._refresh_list()

    def action_cancel_search_or_quit(self) -> None:
        if self.search_mode:
            self.action_toggle_search()
        else:
            self.action_cancel()

    def on_input_changed(self, event: Input.Changed) -> None:
        if self.search_mode and event.input.id == "search-input":
            self._refresh_list()

    def action_approve(self) -> None:
        desired: dict[str, set[str]] = {category: set() for category in _CATEGORIES}
        for entry in self.entries:
            if entry.selected:
                desired[entry.category].add(entry.name)
        self.exit(desired)

    def action_cancel(self) -> None:
        self.cancelled = True
        self.exit(None)


class ConfigureApp(App[dict[str, str] | None]):
    """Step 2: sequential configure prompts for one component's declared
    inputs (FR-014/FR-015) — one input at a time, masked entry when
    `secret: true`. Returns the collected answers, or None if cancelled."""

    CSS = """
    #prompt-label { padding: 1; }
    #prompt-input { margin: 0 1; }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, component_name: str, inputs: list[ComponentInput]) -> None:
        super().__init__()
        self.component_name = component_name
        self.inputs = inputs
        self.answers: dict[str, str] = {}
        self._current_index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="prompt-label")
        yield Input(id="prompt-input")
        yield Footer()

    def on_mount(self) -> None:
        self._show_current_prompt()

    def _show_current_prompt(self) -> None:
        current = self.inputs[self._current_index]
        label = self.query_one("#prompt-label", Static)
        label.update(f"{self.component_name}: {current.label}")
        field = self.query_one("#prompt-input", Input)
        field.value = ""
        field.password = current.secret
        field.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        current = self.inputs[self._current_index]
        self.answers[current.name] = event.value
        self._current_index += 1
        if self._current_index >= len(self.inputs):
            self.exit(self.answers)
        else:
            self._show_current_prompt()

    def action_cancel(self) -> None:
        self.exit(None)
