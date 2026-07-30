"""Core data models for the config picker & configure flow.

Plain data only — no I/O, no rendering. See specs/001-config-picker-tui/data-model.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ComponentState(str, Enum):
    NOT_INSTALLED = "not_installed"
    PENDING_INSTALL = "pending_install"
    INSTALLED = "installed"
    PENDING_REMOVAL = "pending_removal"
    PENDING_CONFIGURATION = "pending_configuration"
    CONFIGURED = "configured"


@dataclass(frozen=True)
class ComponentType:
    name: str
    handler: str  # "content" | "marketplace" | "script"


@dataclass(frozen=True)
class Component:
    type: str
    name: str
    description: str
    category: str | None = None
    recommended: bool = False
    version: str | None = None
    state: ComponentState = ComponentState.NOT_INSTALLED
    origin: str | None = None  # set only on search results ("catalog" or a skill_source name)

    @property
    def key(self) -> str:
        return f"{self.type}:{self.name}"


@dataclass(frozen=True)
class SelectionPlan:
    to_install: list[Component] = field(default_factory=list)
    to_remove: list[Component] = field(default_factory=list)
    already_pending_configuration: list[Component] = field(default_factory=list)

    @property
    def is_noop(self) -> bool:
        return not self.to_install and not self.to_remove


@dataclass(frozen=True)
class ConfigurationInput:
    name: str
    prompt: str
    help_url: str | None = None
    sensitive: bool = False


@dataclass(frozen=True)
class ConfigStep:
    component: Component
    inputs: list[ConfigurationInput]
    reason: str  # "newly_installed" | "user_requested_reconfigure"


@dataclass(frozen=True)
class ApplyResult:
    component: Component
    action: str  # "installed" | "removed"
    ok: bool
    detail: str | None = None


@dataclass(frozen=True)
class VerifyResult:
    component: Component
    ok: bool
    verified: bool
    detail: str | None = None
