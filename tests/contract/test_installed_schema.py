"""Contract test: an installed.json generated from src/core/state_model.py's
InstalledRecord must validate against contracts/installed-schema.json."""

import json
from pathlib import Path

import jsonschema

from src.core.state_model import ContentEntry, InstalledRecord, ScriptConfig, ScriptEntry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "specs" / "001-claude-kit-system" / "contracts" / "installed-schema.json"


def test_generated_installed_record_matches_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    record = InstalledRecord(
        state_version="1",
        last_updated="2026-08-03T12:00:00Z",
        catalog_commit="abc123",
        registry_version="1.0.0",
        cli_version="0.1.0",
        skills={
            "fixture-skill": ContentEntry(
                source="claude-kit",
                installed_hash="deadbeef",
                installed_at="2026-08-03T12:00:00Z",
            )
        },
        tools={
            "fixture-tool": ScriptEntry(
                source="claude-kit",
                version="1.0.0",
                installed_hash="deadbeef",
                config=ScriptConfig(
                    status="done",
                    verified_at="2026-08-03T12:00:00Z",
                    answers={"api_endpoint": "<set>"},
                ),
            )
        },
    )

    instance = json.loads(record.model_dump_json())

    jsonschema.validate(instance=instance, schema=schema)
