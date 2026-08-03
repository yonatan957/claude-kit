"""Script-handler lifecycles for tools & MCP servers (script-lifecycle.md).

A facade over the pieces, kept so the many existing
`from src.installers.script import ...` call sites stay unchanged:

- `script_install`  the install sequence (FR-035/FR-042)
- `script_remove`   the removal sequence (FR-036)
- `script_runner`   shelling out to lifecycle scripts
- `script_mcp`      MCP registration in the shared settings file
- `script_env`      persisting and recovering declared answers
"""

from __future__ import annotations

from src.installers.script_env import load_stored_answers
from src.installers.script_install import install_script_component
from src.installers.script_remove import remove_script_component
from src.installers.script_runner import ScriptInstallError

__all__ = [
    "ScriptInstallError",
    "install_script_component",
    "load_stored_answers",
    "remove_script_component",
]
