"""Engine 1: the Catalog (`registry.json`).

The declarative, versioned source of truth for everything available to
install: each component's metadata, files, required inputs, and the minimum
CLI version needed to use it (data-model.md).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from src.core.models_common import CATEGORIES, CategoryName, Handler


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
    marketplace: str | None = None  # marketplace-handler components only

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
        for category in CATEGORIES:
            expected_handler = declared.get(category)
            for name, component in getattr(self, category).items():
                if expected_handler is not None and component.handler != expected_handler:
                    raise ValueError(
                        f"{category}.{name}: handler '{component.handler}' does not match "
                        f"the declared handler '{expected_handler}' for category '{category}'"
                    )
        return self

    def components_by_category(self) -> dict[CategoryName, dict[str, Component]]:
        return {category: getattr(self, category) for category in CATEGORIES}
