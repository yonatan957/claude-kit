"""Engine 3: the Notification Snapshot (`state.json`).

The small cached result of the most recent background check — one ready-to-
display message plus the comparison details it was built from, and a record of
which findings have already been shown (data-model.md).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
