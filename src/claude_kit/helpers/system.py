"""Talking to the machine: what is on PATH, and running the commands that put it there."""

import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from claude_kit.helpers.consts import TIMEOUT

__all__ = [
    "CommandResult",
    "Tool",
    "ToolStatus",
    "ToolReport",
    "find_binary",
    "is_installed",
    "run",
    "ensure_tool",
]

_NOT_FOUND_CODE = 127
_TIMED_OUT_CODE = 124


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def message(self) -> str:
        return self.stderr.strip() or self.stdout.strip()


@dataclass(frozen=True)
class Tool:
    """A binary the kit shells out to, and the command that installs it."""

    binary: str
    label: str
    install: tuple[str, ...] = ()


class ToolStatus(StrEnum):
    """``PRESENT`` was already there; ``INSTALLED`` is one we just put there."""

    PRESENT = "present"
    INSTALLED = "installed"
    MISSING = "missing"


@dataclass(frozen=True)
class ToolReport:
    tool: Tool
    status: ToolStatus
    path: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status is not ToolStatus.MISSING


def find_binary(name: str) -> str:
    """The executable's full path, or ``""``. Honours PATHEXT, so npm shims resolve."""
    return shutil.which(name) or ""


def is_installed(name: str) -> bool:
    return bool(find_binary(name))


def run(command: Sequence[str], timeout: float = TIMEOUT) -> CommandResult:
    label = " ".join(command)
    executable = find_binary(command[0])
    if not executable:
        return CommandResult(label, _NOT_FOUND_CODE, stderr=f"{command[0]}: not found")
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            label, _TIMED_OUT_CODE, stderr=f"timed out after {timeout:g}s"
        )
    return CommandResult(
        label, completed.returncode, completed.stdout, completed.stderr
    )


def ensure_tool(tool: Tool, install: bool = True) -> ToolReport:
    """Report on ``tool``, installing it first if it is absent."""
    found = find_binary(tool.binary)
    if found:
        return ToolReport(tool, ToolStatus.PRESENT, path=found)

    if not install or not tool.install:
        return ToolReport(
            tool, ToolStatus.MISSING, error=f"{tool.binary} is not on PATH"
        )

    result = run(tool.install)
    found = find_binary(tool.binary)
    if found:
        return ToolReport(tool, ToolStatus.INSTALLED, path=found)
    return ToolReport(
        tool,
        ToolStatus.MISSING,
        error=result.message or f"`{result.command}` left {tool.binary} absent",
    )
