"""Contract test: a state.json generated from src/core/state_model.py's
NotificationSnapshot must validate against contracts/state-schema.json."""

import json
from pathlib import Path

import jsonschema

from src.core.state_model import Findings, NotificationSnapshot

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "specs" / "001-claude-kit-system" / "contracts" / "state-schema.json"


def test_generated_notification_snapshot_matches_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    snapshot = NotificationSnapshot(
        notice_version="1",
        checked_at="2026-08-03T12:00:00Z",
        check_interval_hours=6,
        message="claude-kit: a newer catalog is available; 1 component needs configuration.",
        findings=Findings(
            local_commit="abc123",
            remote_commit="def456",
            local_cli_version="0.1.0",
            latest_cli_version="0.2.0",
            pending_config_count=1,
        ),
        announced=["cli:0.2.0", "catalog:def456"],
    )

    instance = json.loads(snapshot.model_dump_json())

    jsonschema.validate(instance=instance, schema=schema)


def test_null_message_matches_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    snapshot = NotificationSnapshot(
        notice_version="1",
        checked_at="2026-08-03T12:00:00Z",
        check_interval_hours=6,
        message=None,
    )

    instance = json.loads(snapshot.model_dump_json())

    jsonschema.validate(instance=instance, schema=schema)
