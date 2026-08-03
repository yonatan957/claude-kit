"""Registry (Catalog) parsing/validation and the min_cli_version gate (FR-022).

Pure functions only — no I/O (Principle I). Callers supply raw JSON text
already read from disk / synced from the Catalog Repo.
"""

from __future__ import annotations

import json

from src.core.state_model import Registry


class RegistryError(Exception):
    """Raised when a registry.json payload fails to parse, validate, or gate."""


def parse_registry(raw_json: str) -> Registry:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"registry.json is not valid JSON: {exc}") from exc
    try:
        return Registry.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError
        raise RegistryError(f"registry.json failed schema validation: {exc}") from exc


def _parse_version(version: str) -> tuple[int, ...]:
    """Lenient dotted-integer version parser (e.g. "1.2.3" -> (1, 2, 3))."""
    parts: list[int] = []
    for segment in version.split("."):
        digits = ""
        for ch in segment:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def cli_version_satisfies_minimum(cli_version: str, min_cli_version: str) -> bool:
    """True if `cli_version` is >= `min_cli_version`."""
    return _parse_version(cli_version) >= _parse_version(min_cli_version)


def check_min_cli_version(registry: Registry, cli_version: str) -> None:
    """Raise RegistryError (FR-022 gate) if the running CLI is older than the
    catalog's declared minimum."""
    if not cli_version_satisfies_minimum(cli_version, registry.min_cli_version):
        raise RegistryError(
            f"claude-kit {cli_version} is older than this catalog's required "
            f"minimum version {registry.min_cli_version}; upgrade claude-kit before continuing"
        )
