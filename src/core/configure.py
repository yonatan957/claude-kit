"""core.pending(state, registry) -> list[ConfigStep]
core.submit(step, answers, ctx) -> VerifyResult

Configuration inputs are collected by the frontend and passed in here as answers —
this module never prompts. A failed verify leaves the component PENDING_CONFIGURATION
with its install untouched (FR-014 / Constitution I).
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.core.models import (
    Component,
    ComponentState,
    ConfigStep,
    ConfigurationInput,
    VerifyResult,
)
from src.core.transaction import atomic_write, run_transaction

_NON_TYPE_KEYS = {
    "schema_version",
    "version",
    "min_cli_version",
    "hash_algo",
    "catalog_commit",
    "registry_version",
    "cli_version",
}


def pending(state: dict, registry: dict) -> list[ConfigStep]:
    steps: list[ConfigStep] = []
    for type_name, entries in state.items():
        if type_name in _NON_TYPE_KEYS or not isinstance(entries, dict):
            continue
        for name, meta in entries.items():
            config = meta.get("config")
            if not config or config.get("status") != "pending":
                continue
            registry_entry = registry.get(type_name, {}).get(name, {})
            inputs = [ConfigurationInput(**i) for i in registry_entry.get("inputs", [])]
            reason = "user_requested_reconfigure" if config.get("verified_at") else "newly_installed"
            component = Component(
                type=type_name,
                name=name,
                description=registry_entry.get("description", ""),
                category=registry_entry.get("category"),
                recommended=bool(registry_entry.get("recommended", False)),
                version=registry_entry.get("version"),
                state=ComponentState.PENDING_CONFIGURATION,
            )
            steps.append(ConfigStep(component=component, inputs=inputs, reason=reason))
    return steps


def request_reconfigure(state: dict, type_name: str, name: str) -> None:
    """Mark an already-`configured` component as pending again (FR-015), preserving
    `verified_at` so `pending()` reports it as user_requested_reconfigure."""
    entry = state.setdefault(type_name, {}).setdefault(name, {"source": "claude-kit"})
    config = entry.setdefault("config", {})
    config["status"] = "pending"


def _run_script(script: str | None, env: dict[str, str] | None = None) -> tuple[bool, str | None]:
    if not script:
        return True, None
    try:
        subprocess.run(["bash", script], check=True, capture_output=True, text=True, env=env)
    except FileNotFoundError:
        return True, None
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return False, stderr or str(exc)
    return True, None


def default_run_config(
    step: ConfigStep, answers: dict[str, str], registry_entry: dict
) -> tuple[bool, str | None]:
    import os

    script = registry_entry.get("scripts", {}).get("config")
    env = {**os.environ, **answers}
    return _run_script(script, env=env)


def default_run_verify(step: ConfigStep, registry_entry: dict) -> tuple[bool, str | None]:
    return _run_script(registry_entry.get("scripts", {}).get("verify"))


RunConfig = Callable[[ConfigStep, dict[str, str], dict], tuple[bool, str | None]]
RunVerify = Callable[[ConfigStep, dict], tuple[bool, str | None]]


@dataclass
class SubmitContext:
    installed_path: Path
    installed: dict
    registry: dict
    run_config: RunConfig = default_run_config
    run_verify: RunVerify = default_run_verify


def submit(step: ConfigStep, answers: dict[str, str], ctx: SubmitContext) -> VerifyResult:
    registry_entry = ctx.registry.get(step.component.type, {}).get(step.component.name, {})
    outcome: dict = {}

    def do():
        ok, detail = ctx.run_config(step, answers, registry_entry)
        if not ok:
            raise RuntimeError(detail or "config.sh failed")

        verified, verify_detail = ctx.run_verify(step, registry_entry)
        entry = ctx.installed.setdefault(step.component.type, {}).setdefault(
            step.component.name, {"source": "claude-kit"}
        )
        if verified:
            entry["config"] = {"status": "done", "verified_at": datetime.now(UTC).isoformat()}
        else:
            entry["config"] = {"status": "pending"}
        atomic_write(ctx.installed_path, json.dumps(ctx.installed, indent=2))
        outcome["verified"] = verified
        outcome["detail"] = verify_detail
        return verified

    txn = run_transaction(paths=[ctx.installed_path], apply_fn=do)
    if not txn.ok:
        # config.sh itself failed; the component's install is untouched, config stays pending
        return VerifyResult(component=step.component, ok=False, verified=False, detail=txn.detail)

    verified = outcome["verified"]
    return VerifyResult(component=step.component, ok=verified, verified=verified, detail=outcome.get("detail"))
