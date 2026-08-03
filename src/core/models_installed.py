"""Engine 2: the Installed Record (`installed.json`).

The machine's ground truth. Keyed by component name (a map, never a list) so
re-running any install or removal is a pure overwrite — which is what makes
FR-025/FR-037 idempotency structural rather than something callers must
remember to implement carefully (data-model.md).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.core.models_common import ConfigStatus, Source


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
    # Only ever the masked placeholder — real secrets live in env.d/ (FR-039).
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
