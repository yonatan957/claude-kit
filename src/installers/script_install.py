"""The script-handler install sequence (script-lifecycle.md, FR-035/FR-042).

Owns the *order* of the lifecycle and what each outcome means; the mechanics
live in `script_runner`, `script_mcp`, and `script_env`.

Accepts already-collected `answers` as parameters — input collection itself
happens only in commands/ or ui/, never here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from src.core.state_model import CategoryName, Component, ScriptConfig, ScriptEntry
from src.installers.script_env import persist_answers
from src.installers.script_mcp import deregister_mcp_server, register_mcp_server
from src.installers.script_runner import (
    ScriptInstallError,
    component_dir,
    env_var_name,
    lifecycle_script,
    run_script,
    run_step,
)


def _component_content_hash(component: Component) -> str:
    payload = json.dumps(component.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _verify(directory: Path, settings_path: Path, name: str, *, registered: bool, is_update: bool):
    """Run verify.sh and translate its outcome into a config status.

    A fresh install rolls back any just-registered mcp_config on failure so no
    unverified server is left in settings (FR-042); `update`'s re-verify leaves
    the registration alone and only marks the component pending (FR-044).
    """
    script = lifecycle_script(directory, "verify.sh")
    if script is None:
        return "pending", None
    if run_script(script).returncode == 0:
        return "done", datetime.now(UTC)
    if is_update:
        return "pending", None
    if registered:
        deregister_mcp_server(settings_path, name)
    return "failed", None


def install_script_component(
    category: CategoryName,
    name: str,
    component: Component,
    catalog_repo_dir: Path,
    answers: dict[str, str],
    settings_path: Path,
    env_dir: Path,
    source: str = "claude-kit",
    is_update: bool = False,
) -> ScriptEntry:
    """install.sh -> persist answers -> config.sh -> mcp_config -> verify.sh.

    Idempotent: re-running with the same inputs upserts, never duplicates,
    external state. `is_update` selects the FR-044 (pending, registration kept)
    rather than FR-042 (failed, registration rolled back) failure semantics.
    """
    label = f"{category}.{name}"
    directory = component_dir(catalog_repo_dir, category, name)

    run_step(directory, "install.sh", label)
    persist_answers(name, component, answers, env_dir)

    if component.inputs and lifecycle_script(directory, "config.sh") is None:
        raise ScriptInstallError(f"{label}: declares inputs but has no config.sh")
    run_step(directory, "config.sh", label, {env_var_name(k): v for k, v in answers.items()})

    registered = False
    if category == "mcps" and component.mcp_config is not None:
        register_mcp_server(settings_path, name, component.mcp_config)
        registered = True

    status, verified_at = _verify(
        directory, settings_path, name, registered=registered, is_update=is_update
    )

    return ScriptEntry(
        source=source,
        version=component.version,
        installed_hash=_component_content_hash(component),
        config=ScriptConfig(
            status=status,
            verified_at=verified_at,
            answers={k: "<set>" for k in answers},
        ),
    )
