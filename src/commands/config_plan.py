"""Applying a whole approved plan in one pass (FR-012).

Separate from `config_apply`'s per-item dispatch because the batching policy is
its own decision: a failure is collected and reported rather than aborting the
run, and already-applied items are never rolled back — each installer keeps its
own state consistent (script-lifecycle.md).
"""

from __future__ import annotations

from src.commands.config_apply import apply_add, apply_remove
from src.commands.config_collision import default_confirm_collision
from src.core.diffing import DiffPlan
from src.core.state_model import InstalledRecord, Registry


def apply_plan(
    plan: DiffPlan,
    registry: Registry,
    installed: InstalledRecord,
    confirm_collision=default_confirm_collision,
) -> list[str]:
    """One error message per failed item; an empty list means success."""
    errors: list[str] = []
    for item in plan.to_remove:
        try:
            apply_remove(item, registry, installed)
        except Exception as exc:  # noqa: BLE001 - surfaced as a plan error
            errors.append(f"{item.category}.{item.name}: remove failed: {exc}")
    for item in plan.to_add:
        try:
            apply_add(item, registry, installed, confirm_collision)
        except Exception as exc:  # noqa: BLE001 - surfaced as a plan error
            errors.append(f"{item.category}.{item.name}: install failed: {exc}")
    return errors
