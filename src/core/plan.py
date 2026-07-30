"""core.plan(state, registry, selections) -> SelectionPlan

Pure diff of the user's in-progress selections against installed state. No I/O,
no prompting, no printing (Constitution II — Core Has No Voice).
"""

from __future__ import annotations

from src.core.models import ComponentState, SelectionPlan
from src.registry.catalog import has_managed_components, list_components


def plan(state: dict, registry: dict, selections: set[str]) -> SelectionPlan:
    components = list_components(registry, state)

    installed = [c for c in components if c.state != ComponentState.NOT_INSTALLED]
    installed_keys = {c.key for c in installed}

    to_install = [c for c in components if c.key in selections and c.key not in installed_keys]
    to_remove = [c for c in installed if c.key not in selections]
    already_pending_configuration = [
        c for c in installed if c.state == ComponentState.PENDING_CONFIGURATION
    ]

    return SelectionPlan(
        to_install=to_install,
        to_remove=to_remove,
        already_pending_configuration=already_pending_configuration,
    )


def is_first_use(state: dict) -> bool:
    """True iff installed.json has no claude-kit-managed components (FR-009)."""
    return not has_managed_components(state)
