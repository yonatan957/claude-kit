"""Registering and deregistering an MCP server in the shared settings file.

Every write goes through `patch_mcp_servers`, so only the `mcpServers` key's
bytes are ever replaced (FR-038/SC-007). Both operations are idempotent.
"""

from __future__ import annotations

from pathlib import Path

from src.installers.settings_patch import get_mcp_servers, patch_mcp_servers


def _read_settings(settings_path: Path) -> str:
    return settings_path.read_text(encoding="utf-8") if settings_path.exists() else "{}"


def register_mcp_server(settings_path: Path, name: str, mcp_config: dict) -> None:
    raw_settings = _read_settings(settings_path)
    servers = get_mcp_servers(raw_settings)
    servers[name] = mcp_config
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(patch_mcp_servers(raw_settings, servers), encoding="utf-8")


def deregister_mcp_server(settings_path: Path, name: str) -> None:
    if not settings_path.exists():
        return
    raw_settings = _read_settings(settings_path)
    servers = get_mcp_servers(raw_settings)
    if name in servers:
        del servers[name]
        settings_path.write_text(patch_mcp_servers(raw_settings, servers), encoding="utf-8")
