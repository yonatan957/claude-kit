"""Shared literal types for the three JSON engines (data-model.md).

Pure data definitions only — no I/O (Principle I).
"""

from __future__ import annotations

from typing import Literal

Handler = Literal["content", "script", "marketplace"]
CategoryName = Literal["skills", "agents", "plugins", "tools", "mcps"]
Source = Literal["claude-kit", "user"]
ConfigStatus = Literal["pending", "done", "failed"]

CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")
