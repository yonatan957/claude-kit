"""The one add-on shape every source speaks in, and what an installed one adds."""

from claude_kit.components.component import ClaudeComponent, ComponentKind
from claude_kit.components.installed_component import (
    ComponentConfig,
    ConfigStatus,
    InstalledComponent,
)

__all__ = [
    "ComponentKind",
    "ClaudeComponent",
    "ConfigStatus",
    "ComponentConfig",
    "InstalledComponent",
]
