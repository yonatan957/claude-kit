"""What the team's genie manifest offers. It is ours and trusted: a bad entry fails loudly."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_kit.components import ComponentKind
from claude_kit.helpers import GENIE_LABEL, SourceError, SourceUnreachable

__all__ = [
    "GenieInput",
    "GenieEntry",
    "Manifest",
    "load_manifest",
    "parse_manifest",
    "parse_manifest_text",
]

MANIFEST_VERSION = 1


@dataclass(frozen=True)
class GenieInput:
    key: str
    description: str = ""
    help: str = ""
    secret: bool = False
    required: bool = False
    default: str = ""


@dataclass(frozen=True)
class GenieEntry:
    kind: ComponentKind
    name: str
    version: str
    description: str = ""
    inputs: tuple[GenieInput, ...] = ()
    install_scripts: Mapping[str, str] = field(default_factory=dict)
    uninstall_scripts: Mapping[str, str] = field(default_factory=dict)
    mcp_config: dict[str, Any] | None = None


@dataclass(frozen=True)
class Manifest:
    entries: tuple[GenieEntry, ...] = ()
    manifest_dir: Path = Path()

    def find_entry_by_name(self, kind: ComponentKind, name: str) -> GenieEntry | None:
        for entry in self.entries:
            if entry.kind is kind and entry.name == name:
                return entry
        return None

    def search(self, kind: ComponentKind, query: str = "") -> list[GenieEntry]:
        query = query.casefold()
        return [
            entry
            for entry in self.entries
            if entry.kind is kind
            and (
                query in entry.name.casefold() or query in entry.description.casefold()
            )
        ]


def load_manifest(manifest_path: Path) -> Manifest:
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except OSError as failure:
        raise SourceUnreachable(
            GENIE_LABEL, f"cannot read {manifest_path}: {failure}"
        ) from failure
    return parse_manifest_text(manifest_text, str(manifest_path), manifest_path.parent)


def parse_manifest_text(
    manifest_text: str, origin: str, manifest_dir: Path
) -> Manifest:
    try:
        manifest_json = json.loads(manifest_text)
    except json.JSONDecodeError as failure:
        raise SourceError(GENIE_LABEL, f"{origin} is not JSON: {failure}") from failure
    return parse_manifest(manifest_json, origin, manifest_dir)


def parse_manifest(manifest_json: Any, origin: str, manifest_dir: Path) -> Manifest:
    if (
        not isinstance(manifest_json, dict)
        or manifest_json.get("manifest_version") != MANIFEST_VERSION
    ):
        raise SourceError(
            GENIE_LABEL, f"{origin}: manifest_version must be {MANIFEST_VERSION}"
        )
    entries = tuple(
        _parse_entry(entry_json) for entry_json in manifest_json.get("entries", [])
    )
    return Manifest(entries, manifest_dir)


def _parse_entry(entry_json: Any) -> GenieEntry:
    name_for_errors = (
        entry_json.get("name", "?") if isinstance(entry_json, dict) else "?"
    )
    try:
        entry = GenieEntry(
            kind=ComponentKind(entry_json["kind"]),
            name=entry_json["name"],
            version=entry_json["version"],
            description=entry_json.get("description", ""),
            inputs=tuple(
                GenieInput(**input_json) for input_json in entry_json.get("inputs", [])
            ),
            install_scripts=entry_json.get("install", {}),
            uninstall_scripts=entry_json.get("uninstall", {}),
            mcp_config=entry_json.get("mcp"),
        )
    except (AttributeError, KeyError, TypeError, ValueError) as failure:
        raise _entry_error(name_for_errors, f"malformed ({failure})") from failure

    if entry.kind not in (ComponentKind.MCP, ComponentKind.TOOL):
        raise _entry_error(name_for_errors, f"kind {entry.kind} is not mcp or tool")
    if entry.kind is ComponentKind.TOOL and not entry.install_scripts:
        raise _entry_error(
            name_for_errors, "a tool needs install and uninstall scripts"
        )
    if bool(entry.install_scripts) != bool(entry.uninstall_scripts):
        raise _entry_error(name_for_errors, "install and uninstall come together")
    if entry.kind is ComponentKind.MCP and entry.mcp_config is None:
        raise _entry_error(name_for_errors, "an mcp entry needs an mcp block")
    return entry


def _entry_error(name: str, problem: str) -> SourceError:
    return SourceError(GENIE_LABEL, f"manifest entry {name!r}: {problem}")
