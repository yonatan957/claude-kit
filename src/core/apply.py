"""core.apply(plan, registry, ctx) -> list[ApplyResult]

Performs installs then removals, each as its own transaction via the transaction
engine (Constitution I). Order follows the UX design: tools -> plugins -> the rest,
so a failure in one component never rolls back a different, already-committed one.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.core.models import ApplyResult, Component, SelectionPlan
from src.core.transaction import atomic_write, run_transaction

_TYPE_PRIORITY = {"tools": 0, "plugins": 1, "skills": 2, "agents": 2, "mcps": 3}

ComponentAction = Callable[[Component, dict], tuple[bool, str | None]]


def _priority(component: Component) -> int:
    return _TYPE_PRIORITY.get(component.type, 99)


def _run_script(script: str | None) -> tuple[bool, str | None]:
    if not script:
        return True, None
    try:
        subprocess.run(["bash", script], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        return True, None  # no shell/script available on this machine — nothing to run
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return False, f"script failed: {stderr or exc}"
    return True, None


def default_install(component: Component, registry_entry: dict) -> tuple[bool, str | None]:
    return _run_script(registry_entry.get("scripts", {}).get("install"))


def default_remove(component: Component, registry_entry: dict) -> tuple[bool, str | None]:
    script = registry_entry.get("scripts", {}).get("uninstall")
    if not script:
        return True, "no uninstall.sh in the catalog — left on PATH; claude-kit only removes what it owns"
    return _run_script(script)


@dataclass
class ApplyContext:
    installed_path: Path
    installed: dict
    install_component: ComponentAction = default_install
    remove_component: ComponentAction = default_remove


def _mark_installed(installed: dict, component: Component) -> None:
    installed.setdefault(component.type, {})[component.name] = {"source": "claude-kit"}


def _mark_removed(installed: dict, component: Component) -> None:
    installed.get(component.type, {}).pop(component.name, None)


def _run_one(
    component: Component,
    action: str,
    registry_entry: dict,
    action_fn: ComponentAction,
    mark_fn: Callable[[dict, Component], None],
    ctx: ApplyContext,
) -> ApplyResult:
    outcome: dict = {}

    def do():
        ok, detail = action_fn(component, registry_entry)
        if not ok:
            raise RuntimeError(detail or f"{action} failed")
        mark_fn(ctx.installed, component)
        atomic_write(ctx.installed_path, json.dumps(ctx.installed, indent=2))
        outcome["detail"] = detail
        return detail

    txn = run_transaction(paths=[ctx.installed_path], apply_fn=do)
    return ApplyResult(
        component=component,
        action=action,
        ok=txn.ok,
        detail=txn.detail if not txn.ok else outcome.get("detail"),
    )


def apply(plan: SelectionPlan, registry: dict, ctx: ApplyContext) -> list[ApplyResult]:
    results: list[ApplyResult] = []

    for component in sorted(plan.to_install, key=_priority):
        registry_entry = registry.get(component.type, {}).get(component.name, {})
        results.append(
            _run_one(component, "installed", registry_entry, ctx.install_component, _mark_installed, ctx)
        )

    for component in sorted(plan.to_remove, key=_priority):
        registry_entry = registry.get(component.type, {}).get(component.name, {})
        results.append(
            _run_one(component, "removed", registry_entry, ctx.remove_component, _mark_removed, ctx)
        )

    return results
