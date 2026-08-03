"""Script-handler install/removal sequence (script-lifecycle.md, FR-035/
FR-036/FR-042): tools & MCP servers.

Accepts already-collected `answers` as parameters — input collection itself
happens only in commands/ or ui/tui.py, never here.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from src.core.state_model import CategoryName, Component, ScriptConfig, ScriptEntry
from src.installers.secrets import delete_secret_file, read_secret_file, write_secret_file
from src.installers.settings_patch import get_mcp_servers, patch_mcp_servers


class ScriptInstallError(Exception):
    """Raised when a required lifecycle step fails such that no installed.json
    entry should be written."""


def _bash_executable() -> str:
    """Resolve `bash` via PATH ourselves rather than passing the bare name to
    subprocess: on Windows, CreateProcess's search order checks the Windows
    system directory (which holds a WSL launcher stub `bash.exe`) *before*
    PATH, so a bare "bash" can silently resolve to the wrong interpreter."""
    resolved = shutil.which("bash")
    if resolved is None:
        raise ScriptInstallError("no `bash` interpreter found on PATH")
    return resolved


def _component_dir(catalog_repo_dir: Path, category: CategoryName, name: str) -> Path:
    return catalog_repo_dir / category / name


def _lifecycle_script(component_dir: Path, script_name: str) -> Path | None:
    path = component_dir / script_name
    return path if path.exists() else None


def _run_script(path: Path, env_vars: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **(env_vars or {})}
    return subprocess.run(
        [_bash_executable(), path.as_posix()],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        stdin=subprocess.DEVNULL,
    )


def _env_var_name(input_name: str) -> str:
    return input_name.upper().replace("-", "_")


def _component_content_hash(component: Component) -> str:
    payload = json.dumps(component.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_settings(settings_path: Path) -> str:
    return settings_path.read_text(encoding="utf-8") if settings_path.exists() else "{}"


def _register_mcp_server(settings_path: Path, name: str, mcp_config: dict) -> None:
    raw_settings = _read_settings(settings_path)
    servers = get_mcp_servers(raw_settings)
    servers[name] = mcp_config
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(patch_mcp_servers(raw_settings, servers), encoding="utf-8")


def _deregister_mcp_server(settings_path: Path, name: str) -> None:
    if not settings_path.exists():
        return
    raw_settings = _read_settings(settings_path)
    servers = get_mcp_servers(raw_settings)
    if name in servers:
        del servers[name]
        settings_path.write_text(patch_mcp_servers(raw_settings, servers), encoding="utf-8")


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
    """Run the full install sequence: install.sh -> config.sh (with answers as
    env vars) -> mcp_config merge (mcps only) -> verify.sh. Idempotent:
    re-running with the same inputs upserts, never duplicates, external state.

    `is_update` distinguishes `update`'s re-verify of an already-configured
    component (FR-044: failure -> "pending", registration left in place,
    never raises) from a fresh install/add's first verify (FR-042: failure ->
    "failed", any just-registered mcp_config is rolled back immediately).
    """
    component_dir = _component_dir(catalog_repo_dir, category, name)

    install_script = _lifecycle_script(component_dir, "install.sh")
    if install_script is not None:
        result = _run_script(install_script)
        if result.returncode != 0:
            raise ScriptInstallError(f"{category}.{name}: install.sh failed: {result.stderr.strip()}")

    # Persist *every* declared answer (not just secret: true ones) to a
    # restricted per-component file — installed.json can only ever hold the
    # "<set>" placeholder (FR-039), so this is the only place `update` can
    # recover any input's real value to re-run config.sh without re-prompting
    # (research.md #7). Keyed by the input's own declared name, not the
    # derived env var name, so it's read back unambiguously.
    if component.inputs:
        env_file_contents = "\n".join(
            f"{input_def.name}={answers[input_def.name]}"
            for input_def in component.inputs
            if input_def.name in answers
        )
        write_secret_file(env_dir / f"{name}.env", env_file_contents + "\n")

    env_vars = {_env_var_name(k): v for k, v in answers.items()}
    config_script = _lifecycle_script(component_dir, "config.sh")
    if component.inputs and config_script is None:
        raise ScriptInstallError(f"{category}.{name}: declares inputs but has no config.sh")
    if config_script is not None:
        result = _run_script(config_script, env_vars)
        if result.returncode != 0:
            raise ScriptInstallError(f"{category}.{name}: config.sh failed: {result.stderr.strip()}")

    mcp_registered = False
    if category == "mcps" and component.mcp_config is not None:
        _register_mcp_server(settings_path, name, component.mcp_config)
        mcp_registered = True

    verify_script = _lifecycle_script(component_dir, "verify.sh")
    if verify_script is not None:
        result = _run_script(verify_script)
        if result.returncode == 0:
            status, verified_at = "done", datetime.now(UTC)
        elif is_update:
            status, verified_at = "pending", None
        else:
            if mcp_registered:
                _deregister_mcp_server(settings_path, name)
            status, verified_at = "failed", None
    else:
        status, verified_at = "pending", None

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


def load_stored_answers(name: str, env_dir: Path) -> dict[str, str]:
    """Read back a component's persisted answers, keyed by input name, for
    reuse during `update` without re-prompting (research.md #7)."""
    contents = read_secret_file(env_dir / f"{name}.env")
    if contents is None:
        return {}
    answers: dict[str, str] = {}
    for line in contents.splitlines():
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        answers[key] = value
    return answers


def remove_script_component(
    category: CategoryName,
    name: str,
    catalog_repo_dir: Path,
    settings_path: Path,
    env_dir: Path,
) -> None:
    """Run the full removal sequence: deregister mcp_config (mcps only, always
    first) -> uninstall.sh -> delete the secret file. Idempotent: a no-op if
    already fully removed."""
    if category == "mcps":
        _deregister_mcp_server(settings_path, name)

    component_dir = _component_dir(catalog_repo_dir, category, name)
    uninstall_script = _lifecycle_script(component_dir, "uninstall.sh")
    if uninstall_script is not None:
        result = _run_script(uninstall_script)
        if result.returncode != 0:
            raise ScriptInstallError(f"{category}.{name}: uninstall.sh failed: {result.stderr.strip()}")

    delete_secret_file(env_dir / f"{name}.env")
