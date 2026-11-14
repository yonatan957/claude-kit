"""genie: MCP servers and tools from the team's own manifest, first in precedence."""

import getpass
import json
import logging
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

from claude_kit.components import ClaudeComponent, ComponentKind
from claude_kit.helpers import (
    CLAUDE_BINARY,
    CLAUDE_KIT_HOME,
    GENIE_DIR_NAME,
    GENIE_LABEL,
    GENIE_MANIFEST_FILE_NAME,
    MCP_SCOPE,
    NOT_FOUND_CODE,
    TIMED_OUT_CODE,
    CommandResult,
    Conflict,
    SourceError,
    SourceUnreachable,
    UsageError,
    run,
)
from claude_kit.sources.genie.manifest import (
    GenieEntry,
    GenieInput,
    Manifest,
    load_manifest,
)
from claude_kit.sources.source import Source

__all__ = ["GenieSource"]

Prompter = Callable[[GenieInput, str | None], str]

_log = logging.getLogger(__name__)
_UNREACHABLE_CODES = (NOT_FOUND_CODE, TIMED_OUT_CODE)
_NOT_REGISTERED_MESSAGE = "no mcp server named"
# matches {GITLAB_TOKEN}
_PLACEHOLDER_PATTERN = re.compile(r"\{([A-Z_][A-Z0-9_]*)\}")
_KIT_HOME_PLACEHOLDER = "KIT_HOME"
_THIS_PLATFORM = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
_POWERSHELL = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
_NO_VALUES: Mapping[str, str] = MappingProxyType({})


class GenieSource(Source):
    kinds = frozenset({ComponentKind.MCP, ComponentKind.TOOL})

    def __init__(
        self,
        genie_dir: Path = CLAUDE_KIT_HOME / GENIE_DIR_NAME,
        prompter: Prompter | None = None,
        runner: Callable[..., CommandResult] | None = None,
    ) -> None:
        self.genie_dir = genie_dir
        self.prompter = prompter or ask
        self.runner = runner or run
        self._manifest: Manifest | None = None

    @property
    def name(self) -> str:
        return GENIE_LABEL

    def search(self, kind: ComponentKind, query: str = "") -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        return [
            _to_component(entry) for entry in self._get_manifest().search(kind, query)
        ]

    def install(
        self, kind: ComponentKind, name: str, force: bool = False
    ) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        entry = self._get_manifest().find_entry_by_name(kind, name)
        if entry is None:
            return []
        install_script = self._script_for_this_platform(entry, entry.install_scripts)

        was_registered = False
        if entry.mcp_config is not None:
            was_registered = self._claude_mcp("get", entry.name).ok
            if was_registered and not force:
                raise Conflict(
                    f"mcp {entry.name!r} is already registered with Claude Code -- "
                    f"`claude mcp remove {entry.name} --scope {MCP_SCOPE}` first"
                )

        input_values = collect_inputs(entry, self.prompter)
        secret_values = [
            input_values[spec.key]
            for spec in entry.inputs
            if spec.secret and input_values[spec.key]
        ]
        placeholder_values = {
            **input_values,
            _KIT_HOME_PLACEHOLDER: str(CLAUDE_KIT_HOME),
        }
        try:
            mcp_config = _fill_placeholders(entry.mcp_config, placeholder_values)
        except KeyError as unknown:
            raise SourceError(
                self.name, f"{entry.name}: unknown placeholder {unknown.args[0]}"
            ) from None
        if install_script:
            self._run_script(entry, install_script, input_values, secret_values)
        if mcp_config is not None:
            if was_registered:
                self._remove_mcp(entry.name)
            config_json = json.dumps(mcp_config)
            add_args = ["add-json", entry.name, config_json, "--scope", MCP_SCOPE]
            result = self._claude_mcp(
                *add_args, label=f"claude mcp add-json {entry.name}"
            )
            if not result.ok:
                raise self._command_error(result, secret_values)
        return [_to_component(entry)]

    def uninstall(self, kind: ComponentKind, name: str) -> list[ClaudeComponent]:
        if not self.supports(kind):
            return []
        entry = self._get_manifest().find_entry_by_name(kind, name)
        if entry is None:
            return []
        uninstall_script = self._script_for_this_platform(
            entry, entry.uninstall_scripts
        )

        did_remove = False
        if entry.mcp_config is not None:
            did_remove = self._remove_mcp(entry.name)
        if uninstall_script:
            self._run_script(entry, uninstall_script)
            did_remove = True
        return [_to_component(entry)] if did_remove else []

    def _get_manifest(self) -> Manifest:
        if self._manifest is None:
            manifest_path = self.genie_dir / GENIE_MANIFEST_FILE_NAME
            if manifest_path.is_file():
                self._manifest = load_manifest(manifest_path)
            else:
                _log.warning("genie: no local manifest -- run `ck init`")
                self._manifest = Manifest()
        return self._manifest

    def _script_for_this_platform(
        self, entry: GenieEntry, scripts: Mapping[str, str]
    ) -> str:
        if not scripts:
            return ""
        if _THIS_PLATFORM not in scripts:
            raise SourceError(
                self.name, f"{entry.name} has no script for {_THIS_PLATFORM}"
            )
        return scripts[_THIS_PLATFORM]

    def _run_script(
        self,
        entry: GenieEntry,
        script: str,
        input_values: Mapping[str, str] = _NO_VALUES,
        secret_values: Sequence[str] = (),
    ) -> None:
        path = self._get_manifest().manifest_dir / script
        if path.suffix == ".ps1":
            interpreter = _POWERSHELL
        else:
            interpreter = ["bash"]
        env = {
            **input_values,
            "CLAUDE_KIT_HOME": str(CLAUDE_KIT_HOME),
            "GENIE_NAME": entry.name,
            "GENIE_VERSION": entry.version,
        }
        result = self.runner([*interpreter, str(path)], env=env)
        if not result.ok:
            raise self._command_error(
                result, secret_values, action=f"{entry.name}: {script}"
            )

    def _remove_mcp(self, name: str) -> bool:
        result = self._claude_mcp("remove", name, "--scope", MCP_SCOPE)
        if not result.ok and _NOT_REGISTERED_MESSAGE not in result.message.casefold():
            raise self._command_error(result, [])
        return result.ok

    def _claude_mcp(self, *args: str, label: str | None = None) -> CommandResult:
        result = self.runner([CLAUDE_BINARY, "mcp", *args], label=label)
        if result.returncode in _UNREACHABLE_CODES:
            raise self._command_error(result, [])
        return result

    def _command_error(
        self, result: CommandResult, secret_values: Sequence[str], action: str = ""
    ) -> SourceError:
        reason = result.message or f"exit {result.returncode}"
        message = f"{action or result.command} failed: {reason}"
        for secret in secret_values:
            message = message.replace(secret, "***")
        if result.returncode in _UNREACHABLE_CODES:
            return SourceUnreachable(self.name, message)
        return SourceError(self.name, message)


def ask(spec: GenieInput, value_from_env: str | None) -> str:
    if not sys.stdin.isatty():
        return ""
    print(spec.description or spec.key, file=sys.stderr)
    if spec.help:
        print(f"  {spec.help}", file=sys.stderr)
    hint = ""
    if value_from_env:
        hint = " [already set, Enter to keep]"
    elif spec.default:
        hint = f" [{spec.default}]"
    if spec.secret:
        return getpass.getpass(f"{spec.key}{hint}: ").strip()
    return input(f"{spec.key}{hint}: ").strip()


def collect_inputs(entry: GenieEntry, prompter: Prompter) -> dict[str, str]:
    input_values: dict[str, str] = {}
    for spec in entry.inputs:
        value_from_env = os.environ.get(spec.key) or None
        answer = prompter(spec, value_from_env)
        input_values[spec.key] = answer or value_from_env or spec.default
    missing = [
        spec.key
        for spec in entry.inputs
        if spec.required and not input_values[spec.key]
    ]
    if missing:
        raise UsageError(f"{entry.name} needs a value for {', '.join(missing)}")
    return input_values


def _fill_placeholders(template: Any, input_values: Mapping[str, str]) -> Any:
    if isinstance(template, str):
        return _PLACEHOLDER_PATTERN.sub(
            lambda match: input_values[match.group(1)], template
        )
    if isinstance(template, dict):
        return {
            key: _fill_placeholders(item, input_values)
            for key, item in template.items()
        }
    if isinstance(template, list):
        return [_fill_placeholders(item, input_values) for item in template]
    return template


def _to_component(entry: GenieEntry) -> ClaudeComponent:
    return ClaudeComponent(
        kind=entry.kind,
        name=entry.name,
        source=GENIE_LABEL,
        description=entry.description,
        version=entry.version,
    )
