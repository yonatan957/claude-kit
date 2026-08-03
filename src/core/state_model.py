"""Pydantic v2 models for claude-kit's three JSON engines (data-model.md):

- Registry: the remote-synced Catalog (`registry.json`)
- InstalledRecord: the local ground-truth lockfile (`installed.json`)
- NotificationSnapshot: the async notification cache (`state.json`)

Pure data definitions only — no I/O (Principle I). Callers read/write the
underlying files and hand this module raw JSON text / dicts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Handler = Literal["content", "script", "marketplace"]
CategoryName = Literal["skills", "agents", "plugins", "tools", "mcps"]
Source = Literal["claude-kit", "user"]
ConfigStatus = Literal["pending", "done", "failed"]

_CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")


# --- Engine 1: Catalog (registry.json) --------------------------------------


class TypeDeclaration(BaseModel):
    name: CategoryName
    handler: Handler


class PluginMarketplaceCommands(BaseModel):
    add: str
    install: str
    update: str
    remove: str


class ComponentFile(BaseModel):
    path: str
    hash: str


class ComponentInput(BaseModel):
    name: str
    label: str
    secret: bool


class Component(BaseModel):
    description: str
    handler: Handler
    version: str
    files: list[ComponentFile] = Field(default_factory=list)
    inputs: list[ComponentInput] = Field(default_factory=list)
    mcp_config: dict | None = None

    @model_validator(mode="after")
    def _validate_component(self) -> Component:
        if self.handler == "content" and not self.files:
            raise ValueError("content-handler components must declare at least one file")
        names = [i.name for i in self.inputs]
        if len(names) != len(set(names)):
            raise ValueError("input names must be unique within a component")
        return self


class Registry(BaseModel):
    schema_version: str
    version: str
    min_cli_version: str
    types: list[TypeDeclaration]
    plugin_marketplace: PluginMarketplaceCommands
    skills: dict[str, Component] = Field(default_factory=dict)
    agents: dict[str, Component] = Field(default_factory=dict)
    plugins: dict[str, Component] = Field(default_factory=dict)
    tools: dict[str, Component] = Field(default_factory=dict)
    mcps: dict[str, Component] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_handlers_match_declared_types(self) -> Registry:
        declared = {t.name: t.handler for t in self.types}
        for category in _CATEGORIES:
            expected_handler = declared.get(category)
            for name, component in getattr(self, category).items():
                if expected_handler is not None and component.handler != expected_handler:
                    raise ValueError(
                        f"{category}.{name}: handler '{component.handler}' does not match "
                        f"the declared handler '{expected_handler}' for category '{category}'"
                    )
        return self

    def components_by_category(self) -> dict[CategoryName, dict[str, Component]]:
        return {category: getattr(self, category) for category in _CATEGORIES}


# --- Engine 2: Installed Record (installed.json) ----------------------------


class ContentEntry(BaseModel):
    source: Source
    installed_hash: str
    installed_at: datetime


class PluginEntry(BaseModel):
    source: Source
    marketplace: str
    version: str
    enabled: bool


class ScriptConfig(BaseModel):
    status: ConfigStatus
    verified_at: datetime | None = None
    answers: dict[str, Literal["<set>"]] = Field(default_factory=dict)


class ScriptEntry(BaseModel):
    source: Source
    version: str
    installed_hash: str
    config: ScriptConfig


class InstalledRecord(BaseModel):
    state_version: str
    last_updated: datetime
    catalog_commit: str
    registry_version: str
    cli_version: str
    skills: dict[str, ContentEntry] = Field(default_factory=dict)
    agents: dict[str, ContentEntry] = Field(default_factory=dict)
    plugins: dict[str, PluginEntry] = Field(default_factory=dict)
    tools: dict[str, ScriptEntry] = Field(default_factory=dict)
    mcps: dict[str, ScriptEntry] = Field(default_factory=dict)


# --- Engine 3: Notification Snapshot (state.json) ---------------------------


class Findings(BaseModel):
    local_commit: str = ""
    remote_commit: str = ""
    local_cli_version: str = ""
    latest_cli_version: str = ""
    pending_config_count: int = 0


class NotificationSnapshot(BaseModel):
    notice_version: str
    checked_at: datetime
    check_interval_hours: float
    message: str | None = None
    findings: Findings = Field(default_factory=Findings)
    announced: list[str] = Field(default_factory=list)
