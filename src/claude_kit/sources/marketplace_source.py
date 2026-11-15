"""One Claude Code plugin marketplace. ``index.build_sources`` makes one per marketplace.

Claude Code does the real work -- cloning the marketplace and installing the plugin.
A source only registers its marketplace and reads the catalog Claude Code cloned.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import (
    CLAUDE_BINARY,
    KNOWN_MARKETPLACES_FILE,
    MARKETPLACE_LABEL,
    CommandResult,
    SourceError,
    run,
)
from claude_kit.sources.source import InitReport, Source

__all__ = ["MarketplaceSource"]

_CATALOG_PATH = Path(".claude-plugin") / "marketplace.json"


class MarketplaceSource(Source):
    kinds = frozenset({ComponentKind.PLUGIN})

    def __init__(
        self,
        marketplace: str,
        url: str,
        known_marketplaces_file: Path = KNOWN_MARKETPLACES_FILE,
        runner: Callable[..., CommandResult] | None = None,
    ) -> None:
        self.marketplace = marketplace
        self.url = url
        self.known_marketplaces_file = known_marketplaces_file
        self.runner = runner or run

    @property
    def name(self) -> str:
        return self.marketplace

    def init(self, home: Path, install_missing: bool) -> InitReport:
        registered = self.marketplace in _read_json(self.known_marketplaces_file)
        action = ["update", self.marketplace] if registered else ["add", self.url]
        result = self._claude_plugin("marketplace", *action)
        if not result.ok:
            reason = result.message or f"exit {result.returncode}"
            return InitReport("!", self.name, f"could not {action[0]} -- {reason}")
        done = "updated" if registered else "added"
        return InitReport("✓", self.name, f"{done} from {self.url}")

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        query = query.casefold()
        return [
            self._to_component(plugin)
            for plugin in self._plugins()
            if query in plugin["name"].casefold()
            or query in plugin.get("description", "").casefold()
        ]

    def install(
        self, kind: ComponentKind, name: str, force: bool = False
    ) -> list[ClaudeComponent]:
        return self._plugin_action("install", kind, name)

    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        return self._plugin_action("uninstall", kind, name)

    def _plugin_action(
        self, action: str, kind: ComponentKind, name: str
    ) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        plugin = next((one for one in self._plugins() if one["name"] == name), None)
        if plugin is None:
            return []
        result = self._claude_plugin(action, f"{name}@{self.marketplace}")
        if not result.ok:
            reason = result.message or f"exit {result.returncode}"
            raise SourceError(self.name, f"{result.command} failed: {reason}")
        return [self._to_component(plugin)]

    def _plugins(self) -> list[dict[str, Any]]:
        """The catalog Claude Code cloned; empty until `ck init` registered it."""
        known = _read_json(self.known_marketplaces_file)
        location = known.get(self.marketplace, {}).get("installLocation")
        if not location:
            return []
        plugins: list[dict[str, Any]] = _read_json(Path(location) / _CATALOG_PATH).get(
            "plugins", []
        )
        return plugins

    def _claude_plugin(self, *args: str) -> CommandResult:
        return self.runner([CLAUDE_BINARY, "plugin", *args])

    def _to_component(self, plugin: dict[str, Any]) -> ClaudeComponent:
        return ClaudeComponent(
            kind=ComponentKind.PLUGIN,
            name=plugin["name"],
            source=self.name,
            description=plugin.get("description", ""),
            version=plugin.get("version", ""),
        )


def _read_json(path: Path) -> dict[str, Any]:
    """A file that is missing answers empty: not cloned yet, or `ck init` never ran."""
    if not path.is_file():
        return {}
    try:
        content: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as failure:
        raise SourceError(MARKETPLACE_LABEL, f"{path} is not JSON: {failure}") from None
    return content
