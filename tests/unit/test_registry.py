"""Unit tests for src/core/registry.py: parsing/validation and the
min_cli_version gate (FR-022)."""

import json
from pathlib import Path

import pytest

from src.core.registry import (
    RegistryError,
    check_min_cli_version,
    cli_version_satisfies_minimum,
    parse_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"


def _fixture_json() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_registry_accepts_valid_fixture():
    registry = parse_registry(_fixture_json())
    assert registry.version == "1.0.0"
    assert "fixture-skill" in registry.skills
    assert "fixture-tool" in registry.tools
    assert "fixture-mcp" in registry.mcps
    assert "fixture-plugin" in registry.plugins


def test_parse_registry_rejects_invalid_json():
    with pytest.raises(RegistryError):
        parse_registry("{not valid json")


def test_parse_registry_rejects_handler_mismatch_with_declared_type():
    data = json.loads(_fixture_json())
    # fixture-skill's category ("skills") declares handler "content"; corrupt
    # the component's own handler so it disagrees.
    data["skills"]["fixture-skill"]["handler"] = "script"

    with pytest.raises(RegistryError):
        parse_registry(json.dumps(data))


def test_parse_registry_rejects_content_component_with_no_files():
    data = json.loads(_fixture_json())
    data["skills"]["fixture-skill"]["files"] = []

    with pytest.raises(RegistryError):
        parse_registry(json.dumps(data))


def test_parse_registry_rejects_duplicate_input_names():
    data = json.loads(_fixture_json())
    data["tools"]["fixture-tool"]["inputs"] = [
        {"name": "api_endpoint", "label": "A", "secret": False},
        {"name": "api_endpoint", "label": "B", "secret": False},
    ]

    with pytest.raises(RegistryError):
        parse_registry(json.dumps(data))


@pytest.mark.parametrize(
    ("current", "minimum", "expected"),
    [
        ("1.0.0", "1.0.0", True),
        ("1.2.0", "1.0.0", True),
        ("0.9.0", "1.0.0", False),
        ("1.0.0", "1.0.1", False),
        ("2.0.0", "1.9.9", True),
    ],
)
def test_cli_version_satisfies_minimum(current, minimum, expected):
    assert cli_version_satisfies_minimum(current, minimum) is expected


def test_check_min_cli_version_passes_when_satisfied():
    registry = parse_registry(_fixture_json())
    check_min_cli_version(registry, cli_version="0.1.0")  # fixture requires 0.1.0


def test_check_min_cli_version_raises_when_too_old():
    registry = parse_registry(_fixture_json())
    with pytest.raises(RegistryError):
        check_min_cli_version(registry, cli_version="0.0.1")
