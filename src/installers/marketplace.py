"""Marketplace-handler installer (FR-034): delegates plugin add/install/
update/remove to the catalog's own `plugin_marketplace` command templates via
subprocess — never re-implements the plugin mechanism itself.
"""

from __future__ import annotations

import shlex
import subprocess

from src.core.state_model import Component, PluginEntry, PluginMarketplaceCommands


class MarketplaceInstallError(Exception):
    """Raised when a delegated plugin marketplace command fails."""


def _run(command_template: str, *, name: str, marketplace: str) -> subprocess.CompletedProcess:
    command = command_template.format(name=name, marketplace=marketplace)
    return subprocess.run(shlex.split(command), capture_output=True, text=True, check=False)


def install_plugin(
    name: str,
    component: Component,
    commands: PluginMarketplaceCommands,
    source: str = "claude-kit",
) -> PluginEntry:
    """Add the plugin's marketplace (idempotent by contract) then install the
    plugin from it."""
    marketplace = component.marketplace
    if not marketplace:
        raise MarketplaceInstallError(f"plugins.{name} does not declare a marketplace")

    add_result = _run(commands.add, name=name, marketplace=marketplace)
    if add_result.returncode != 0:
        raise MarketplaceInstallError(
            f"plugins.{name}: marketplace add failed: {add_result.stderr.strip()}"
        )

    install_result = _run(commands.install, name=name, marketplace=marketplace)
    if install_result.returncode != 0:
        raise MarketplaceInstallError(
            f"plugins.{name}: install failed: {install_result.stderr.strip()}"
        )

    return PluginEntry(source=source, marketplace=marketplace, version=component.version, enabled=True)


def update_plugin(name: str, entry: PluginEntry, commands: PluginMarketplaceCommands) -> None:
    result = _run(commands.update, name=name, marketplace=entry.marketplace)
    if result.returncode != 0:
        raise MarketplaceInstallError(f"plugins.{name}: update failed: {result.stderr.strip()}")


def remove_plugin(name: str, entry: PluginEntry, commands: PluginMarketplaceCommands) -> None:
    """Idempotent: the delegated remove command is expected to no-op if the
    plugin is already gone (script-lifecycle.md idempotency contract)."""
    result = _run(commands.remove, name=name, marketplace=entry.marketplace)
    if result.returncode != 0:
        raise MarketplaceInstallError(f"plugins.{name}: remove failed: {result.stderr.strip()}")
