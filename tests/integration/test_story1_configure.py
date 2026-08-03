"""Integration test: Step 2 sequential configure — masked secret entry,
`installed.json` shows `config.status = "done"`, `env.d/<name>.env` holds the
real secret, and `installed.json`'s `answers` field is the literal string
`"<set>"` (FR-014-FR-016)."""

import json
from pathlib import Path

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from src.core.state_model import Registry
from src.installers.script import install_script_component
from src.ui.configure import collect_inputs

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


def _load_mcp():
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    return registry.mcps["fixture-mcp"]


def _collect(inputs, typed: str):
    with create_pipe_input() as pipe:
        pipe.send_text(typed)
        with create_app_session(input=pipe, output=DummyOutput()):
            return collect_inputs("fixture-mcp", inputs)


def test_step2_declares_the_secret_input_as_masked():
    mcp = _load_mcp()
    secret_flags = {i.name: i.secret for i in mcp.inputs}

    # The masking itself is prompt_toolkit's `is_password`, driven directly by
    # this flag in `collect_inputs` — so the contract worth asserting here is
    # that the catalog marks the credential secret in the first place.
    assert secret_flags == {"api_key": True}


def test_step2_answers_flow_into_installed_json_and_secret_file(tmp_path):
    mcp = _load_mcp()

    answers = _collect(mcp.inputs, "s3cr3t-value\r")
    assert answers == {"api_key": "s3cr3t-value"}

    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"

    entry = install_script_component(
        "mcps", "fixture-mcp", mcp, CATALOG_DIR, answers, settings_path, env_dir
    )

    assert entry.config.status == "done"
    assert entry.config.answers == {"api_key": "<set>"}  # never the real value (FR-016/FR-039)

    secret_file = env_dir / "fixture-mcp.env"
    assert secret_file.exists()
    assert "s3cr3t-value" in secret_file.read_text(encoding="utf-8")

    installed_json = json.dumps({"mcps": {"fixture-mcp": json.loads(entry.model_dump_json())}})
    assert "s3cr3t-value" not in installed_json  # real secret never reaches the tracking file
