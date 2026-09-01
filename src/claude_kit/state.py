"""The cached result of ``ck status``: what is behind, and what was last announced."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["VersionStatus", "KitState", "read_state", "write_state"]


@dataclass(frozen=True)
class VersionStatus:
    installed: str = ""
    available: str = ""
    action: str = ""
    behind_by: int | None = None


@dataclass(frozen=True)
class KitState:
    notice_version: int = 1
    checked_at: str = ""
    check_interval_hours: int = 24
    message: str = ""
    versions: dict[str, VersionStatus] = field(default_factory=dict)
    announced: dict[str, str] = field(default_factory=dict)


def read_state(path: Path | str) -> KitState:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return KitState()
    return _to_state(payload) if isinstance(payload, dict) else KitState()


def write_state(path: Path | str, state: KitState) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = path.with_suffix(path.suffix + ".tmp")
    written.write_text(
        json.dumps(
            state,
            default=lambda obj: {
                name: value
                for name, value in vars(obj).items()
                if value not in ("", None)
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(written, path)


def _to_state(payload: dict[str, Any]) -> KitState:
    default = KitState()
    notice_version = payload.get("notice_version")
    check_interval_hours = payload.get("check_interval_hours")
    versions = payload.get("versions")
    announced = payload.get("announced")
    return KitState(
        notice_version=(
            notice_version if is_int(notice_version) else default.notice_version
        ),
        checked_at=str(payload.get("checked_at") or ""),
        check_interval_hours=(
            check_interval_hours
            if is_int(check_interval_hours)
            else default.check_interval_hours
        ),
        message=str(payload.get("message") or ""),
        versions={
            name: _to_status(status)
            for name, status in (versions if is_dict(versions) else {}).items()
            if is_dict(status)
        },
        announced={
            name: str(version)
            for name, version in (announced if is_dict(announced) else {}).items()
        },
    )


def _to_status(status: dict[str, Any]) -> VersionStatus:
    behind_by = status.get("behind_by")
    return VersionStatus(
        installed=str(status.get("installed") or ""),
        available=str(status.get("available") or ""),
        action=str(status.get("action") or ""),
        behind_by=behind_by if is_int(behind_by) else None,
    )


def is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
