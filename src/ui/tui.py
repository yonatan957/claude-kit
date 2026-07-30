"""prompt_toolkit frontend: picker, search overlay, approve row, configure wizard.

Constitution II (Core Has No Voice): every decision here is a render of a `core/`
function's return value. `ConfigFlowSession` holds only orchestration state (current
selections, which screen) and drives `core.plan` / `core.apply` / `core.pending` /
`core.submit` directly — it never mutates a file itself. The interactive
`Application` built by `run_config_flow` is a thin, largely untestable shell around
it; `ConfigFlowSession` is what tests drive to exercise the whole flow headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.shortcuts import input_dialog, radiolist_dialog

from src.core.apply import ApplyContext, apply
from src.core.configure import SubmitContext, pending, request_reconfigure, submit
from src.core.models import (
    ApplyResult,
    Component,
    ComponentState,
    ConfigStep,
    SelectionPlan,
    VerifyResult,
)
from src.core.plan import is_first_use, plan
from src.registry.catalog import list_components, search_components

APPROVE_ROW_KEY = "__approve__"


@dataclass
class PickerRow:
    kind: str  # "header" | "component" | "approve"
    label: str
    component: Component | None = None
    marker: str | None = None  # e.g. "+ will install", "- WILL BE REMOVED"


@dataclass
class ConfigFlowSession:
    """Everything the picker/configure flow needs, with zero terminal I/O.

    This is `core.plan(state, registry, selections) -> ChangePlan` and friends,
    held together with the one piece of state a human interaction needs across
    calls: which components are currently checked.
    """

    registry: dict
    installed: dict
    installed_path: object  # pathlib.Path — kept loose to avoid importing Path just for typing
    component_type: str | None = None
    selections: set[str] = field(default_factory=set)
    # Injectable install/config/verify strategies — default to the real
    # subprocess-backed ones; tests substitute fakes so no real shell is needed.
    install_component: object = None
    remove_component: object = None
    run_config: object = None
    run_verify: object = None

    # --- selection state -------------------------------------------------

    def components(self) -> list[Component]:
        return list_components(self.registry, self.installed, self.component_type)

    def needs_recommended_prompt(self) -> bool:
        return is_first_use(self.installed)

    def apply_recommended_defaults(self) -> None:
        self.selections = {c.key for c in self.components() if c.recommended}

    def initialize_selections_from_installed(self) -> None:
        self.selections = {
            c.key for c in self.components() if c.state != ComponentState.NOT_INSTALLED
        }

    def toggle(self, key: str) -> None:
        if key in self.selections:
            self.selections.discard(key)
        else:
            self.selections.add(key)

    # --- plan / approve ----------------------------------------------------

    def current_plan(self) -> SelectionPlan:
        return plan(self.installed, self.registry, self.selections)

    def approve(self) -> list[ApplyResult]:
        kwargs = {}
        if self.install_component is not None:
            kwargs["install_component"] = self.install_component
        if self.remove_component is not None:
            kwargs["remove_component"] = self.remove_component
        ctx = ApplyContext(installed_path=self.installed_path, installed=self.installed, **kwargs)
        return apply(self.current_plan(), self.registry, ctx)

    # --- configure -----------------------------------------------------

    def pending_steps(self) -> list[ConfigStep]:
        return pending(self.installed, self.registry)

    def submit_step(self, step: ConfigStep, answers: dict[str, str]) -> VerifyResult:
        kwargs = {}
        if self.run_config is not None:
            kwargs["run_config"] = self.run_config
        if self.run_verify is not None:
            kwargs["run_verify"] = self.run_verify
        ctx = SubmitContext(
            installed_path=self.installed_path, installed=self.installed, registry=self.registry, **kwargs
        )
        return submit(step, answers, ctx)

    def request_reconfigure(self, component: Component) -> None:
        request_reconfigure(self.installed, component.type, component.name)

    # --- search ----------------------------------------------------------

    def search(self, query: str, skill_sources: list[dict] | None = None, search_runner=None) -> list[Component]:
        return search_components(query, self.registry, self.installed, skill_sources, search_runner)


# --- render helpers (pure — drive the real Application AND are unit-testable) ---


def build_picker_rows(session: ConfigFlowSession, pinned_search_results: list[Component] | None = None) -> list[PickerRow]:
    """One flat list: pinned search results, then a section per component type,
    each with a live selection counter, ending in the fixed Approve & install row."""
    rows: list[PickerRow] = []
    current_plan = session.current_plan()
    pending_removal_keys = {c.key for c in current_plan.to_remove}
    pending_install_keys = {c.key for c in current_plan.to_install}

    if pinned_search_results:
        selected = sum(1 for c in pinned_search_results if c.key in session.selections)
        rows.append(PickerRow(kind="header", label=f"Search results ({selected} selected)"))
        for c in pinned_search_results:
            rows.append(_component_row(c, session, pending_install_keys, pending_removal_keys))

    by_type: dict[str, list[Component]] = {}
    for c in session.components():
        by_type.setdefault(c.type, []).append(c)

    for type_name in sorted(by_type):
        components = by_type[type_name]
        selected = sum(1 for c in components if c.key in session.selections)
        rows.append(PickerRow(kind="header", label=f"{type_name.title()} ({selected} selected)"))
        for c in components:
            rows.append(_component_row(c, session, pending_install_keys, pending_removal_keys))

    removal_count = len(current_plan.to_remove)
    approve_label = "Approve & install"
    if removal_count:
        approve_label += f" · {removal_count} removal{'s' if removal_count != 1 else ''}"
    rows.append(PickerRow(kind="approve", label=approve_label))
    return rows


def _component_row(
    c: Component, session: ConfigFlowSession, pending_install_keys: set[str], pending_removal_keys: set[str]
) -> PickerRow:
    marker = None
    if c.key in pending_install_keys:
        marker = "+ will install"
    elif c.key in pending_removal_keys:
        marker = "- WILL BE REMOVED (was installed)"
    checked = "x" if c.key in session.selections else " "
    origin = f" [{c.origin}]" if c.origin and c.origin != "catalog" else ""
    return PickerRow(kind="component", label=f"[{checked}] {c.name}{origin}", component=c, marker=marker)


def build_summary_lines(apply_results: list[ApplyResult], configure_results: list[VerifyResult]) -> list[str]:
    """FR-013: distinguish installed / removed / configured / pending, plus FR-014's
    partial-removal detail (e.g. no uninstall.sh) surfaced explicitly."""
    lines: list[str] = []
    installed_count = sum(1 for r in apply_results if r.action == "installed" and r.ok)
    removed_count = sum(1 for r in apply_results if r.action == "removed" and r.ok)
    configured_count = sum(1 for r in configure_results if r.verified)
    pending_count = sum(1 for r in configure_results if not r.verified)

    lines.append(
        f"{installed_count} installed · {removed_count} removed · "
        f"{configured_count} configured · {pending_count} pending"
    )
    for r in apply_results:
        if r.detail:
            lines.append(f"  {r.component.name}: {r.detail}")
    for r in configure_results:
        if not r.verified and r.detail:
            lines.append(f"  {r.component.name}: still pending — {r.detail}")
    return lines


# --- the interactive shell (thin; not unit-tested headlessly) ---


def _run_picker(session: ConfigFlowSession) -> bool:
    """Returns True if the user approved, False if they quit (ctrl-c)."""
    state = {"cursor": 0, "approved": False, "quit": False, "pinned": []}

    def rows() -> list[PickerRow]:
        return build_picker_rows(session, pinned_search_results=state["pinned"])

    def render():
        lines = []
        for i, row in enumerate(rows()):
            prefix = "> " if i == state["cursor"] else "  "
            suffix = f"  {row.marker}" if row.marker else ""
            lines.append(f"{prefix}{row.label}{suffix}")
        lines.append("")
        lines.append("↑↓ move · enter: select / approve on last row · tab: search · ctrl-c: quit")
        return "\n".join(lines)

    control = FormattedTextControl(text=render)
    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        state["cursor"] = max(0, state["cursor"] - 1)

    @kb.add("down")
    def _(event):
        state["cursor"] = min(len(rows()) - 1, state["cursor"] + 1)

    @kb.add("tab")
    def _(event):
        query = input_dialog(title="Search", text="Query:").run()
        if query:
            state["pinned"] = session.search(query)
            state["cursor"] = 0

    @kb.add("enter")
    def _(event):
        row = rows()[state["cursor"]]
        if row.kind == "approve":
            state["approved"] = True
            event.app.exit()
        elif row.kind == "component" and row.component is not None:
            session.toggle(row.component.key)

    @kb.add("c-c")
    def _(event):
        state["quit"] = True
        event.app.exit()

    app = Application(layout=Layout(HSplit([Window(control)])), key_bindings=kb, full_screen=False)
    app.run()
    return state["approved"]


def _run_configure_wizard(session: ConfigFlowSession) -> list[VerifyResult]:
    results: list[VerifyResult] = []
    for step in session.pending_steps():
        answers: dict[str, str] = {}
        for inp in step.inputs:
            value = input_dialog(title=inp.prompt, text=inp.prompt, password=inp.sensitive).run()
            answers[inp.name] = value or ""
        results.append(session.submit_step(step, answers))
    return results


def run_config_flow(
    registry: dict,
    installed: dict,
    installed_path,
    component_type: str | None = None,
    force_recommended: bool = False,
) -> None:
    session = ConfigFlowSession(
        registry=registry, installed=installed, installed_path=installed_path, component_type=component_type
    )

    if force_recommended:
        session.apply_recommended_defaults()
    elif session.needs_recommended_prompt():
        choice = radiolist_dialog(
            title="How would you like to set up?",
            text="",
            values=[("recommended", "Recommended"), ("custom", "Custom")],
        ).run()
        if choice == "recommended":
            session.apply_recommended_defaults()
        else:
            session.initialize_selections_from_installed()
    else:
        session.initialize_selections_from_installed()

    current_plan = session.current_plan()
    apply_results: list[ApplyResult] = []
    if not current_plan.is_noop:
        approved = _run_picker(session)
        if not approved:
            return  # ctrl-c: nothing applied, nothing pending changed
        apply_results = session.approve()

    configure_results = _run_configure_wizard(session)

    for line in build_summary_lines(apply_results, configure_results):
        print(line)  # noqa: T201 - the one place output is allowed: the frontend's own entrypoint
