"""A component that is on disk, and what claude-kit knows about putting it there.

``ClaudeComponent`` is what a source says about a package. This is that, plus
the facts that only exist once it has been installed.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from claude_kit.components.component import ClaudeComponent

__all__ = ["ConfigStatus", "ComponentConfig", "InstalledComponent"]

_NO_KEYS: Mapping[str, bool] = MappingProxyType({})


class ConfigStatus(StrEnum):
    NONE = "none"
    PENDING = "pending"
    DONE = "done"


@dataclass(frozen=True)
class ComponentConfig:

    status: ConfigStatus = ConfigStatus.NONE
    verified_at: str = ""
    keys: Mapping[str, bool] = _NO_KEYS


@dataclass(frozen=True)
class InstalledComponent:
    component: ClaudeComponent
    installed_at: str
    installed_hash: str = ""
    updated_at: str = ""
    marketplace: str = ""
    enabled: bool = True
    config: ComponentConfig = field(default_factory=ComponentConfig)
