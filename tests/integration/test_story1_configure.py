"""Integration test: Step 2 sequential configure — masked secret entry,
`installed.json` shows `config.status = "done"`, `env.d/<name>.env` holds the
real secret, and `installed.json`'s `answers` field is the literal string
`"<set>"` (FR-014-FR-016)."""

import json
from pathlib import Path

from src.core.state_model import Registry
from src.installers.script import install_script_component
from src.ui.tui import ConfigureApp

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


async def test_step2_masks_secret_entry_on_screen():
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    mcp = registry.mcps["fixture-mcp"]

    app = ConfigureApp("fixture-mcp", mcp.inputs)
    async with app.run_test() as pilot:
        await pilot.pause()
        field = app.query_one("#prompt-input")
        assert field.password is True  # the only declared input (api_key) is secret


async def test_step2_answers_flow_into_installed_json_and_secret_file(tmp_path):
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    mcp = registry.mcps["fixture-mcp"]

    app = ConfigureApp("fixture-mcp", mcp.inputs)
    async with app.run_test() as pilot:
        await pilot.pause()
        for ch in "s3cr3t-value":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

    answers = app.answers
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
