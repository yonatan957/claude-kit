"""Running a component's lifecycle scripts (script-lifecycle.md).

Everything that shells out lives here, so the install/remove sequences read as
policy rather than as subprocess plumbing. Scripts always run with stdin closed
— a lifecycle script must never be able to block waiting for input (Principle
II).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from src.core.state_model import CategoryName


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


def component_dir(catalog_repo_dir: Path, category: CategoryName, name: str) -> Path:
    return catalog_repo_dir / category / name


def lifecycle_script(directory: Path, script_name: str) -> Path | None:
    path = directory / script_name
    return path if path.exists() else None


def env_var_name(input_name: str) -> str:
    return input_name.upper().replace("-", "_")


def run_script(path: Path, env_vars: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **(env_vars or {})}
    return subprocess.run(
        [_bash_executable(), path.as_posix()],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        stdin=subprocess.DEVNULL,
    )


def run_step(
    directory: Path,
    script_name: str,
    label: str,
    env_vars: dict[str, str] | None = None,
) -> bool:
    """Run one lifecycle script if it exists, raising on a non-zero exit.

    Returns False when the script is absent (a legitimate no-op), True when it
    ran successfully.
    """
    script = lifecycle_script(directory, script_name)
    if script is None:
        return False
    result = run_script(script, env_vars)
    if result.returncode != 0:
        raise ScriptInstallError(f"{label}: {script_name} failed: {result.stderr.strip()}")
    return True
