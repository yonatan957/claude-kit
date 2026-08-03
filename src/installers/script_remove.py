"""The script-handler removal sequence (script-lifecycle.md, FR-036).

Deregistration happens first and unconditionally, so a failing `uninstall.sh`
can never strand a live MCP registration pointing at a half-removed component.
"""

from __future__ import annotations

from pathlib import Path

from src.core.state_model import CategoryName
from src.installers.script_mcp import deregister_mcp_server
from src.installers.script_runner import component_dir, run_step
from src.installers.secrets import delete_secret_file


def remove_script_component(
    category: CategoryName,
    name: str,
    catalog_repo_dir: Path,
    settings_path: Path,
    env_dir: Path,
) -> None:
    """Deregister mcp_config (always first) -> uninstall.sh -> delete secrets.
    Idempotent: a no-op if already fully removed."""
    if category == "mcps":
        deregister_mcp_server(settings_path, name)

    directory = component_dir(catalog_repo_dir, category, name)
    run_step(directory, "uninstall.sh", f"{category}.{name}")

    delete_secret_file(env_dir / f"{name}.env")
