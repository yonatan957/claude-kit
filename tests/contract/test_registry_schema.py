"""Contract test: the fixture registry.json must validate against
contracts/registry-schema.json (the CLI's own catalog contract)."""

import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "specs" / "001-claude-kit-system" / "contracts" / "registry-schema.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"


def test_fixture_registry_matches_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    instance = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    jsonschema.validate(instance=instance, schema=schema)
