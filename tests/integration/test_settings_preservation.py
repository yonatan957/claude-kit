"""Integration test: `claude_settings.json` is byte-for-byte identical
outside the `mcpServers` key before vs. after an MCP install (FR-038/
SC-007)."""

import json
from pathlib import Path

from src.core.state_model import Registry
from src.installers.script import install_script_component, remove_script_component

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()

PRE_EXISTING_SETTINGS = """{
  "theme":   "dark",
  "mcpServers": {
    "some-other-server": { "command": "foo", "args": ["bar"] }
  },
  "customToolSetting": {
    "nested": [1, 2, 3],
    "weird   spacing": true
  },
  "featureFlags": ["a", "b", "c"]
}
"""


def test_settings_byte_identical_outside_mcp_servers_after_install(tmp_path):
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    mcp = registry.mcps["fixture-mcp"]

    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(PRE_EXISTING_SETTINGS, encoding="utf-8")
    env_dir = tmp_path / ".claude-kit" / "env.d"

    install_script_component(
        "mcps", "fixture-mcp", mcp, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )

    after = settings_path.read_text(encoding="utf-8")

    assert '"theme":   "dark",' in after
    assert '"nested": [1, 2, 3],' in after
    assert '"weird   spacing": true' in after
    assert '"featureFlags": ["a", "b", "c"]' in after
    # The pre-existing sibling MCP server registration must survive untouched.
    parsed = json.loads(after)
    assert parsed["mcpServers"]["some-other-server"] == {"command": "foo", "args": ["bar"]}
    assert "fixture-mcp" in parsed["mcpServers"]


def test_settings_byte_identical_outside_mcp_servers_after_remove(tmp_path):
    registry = Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))
    mcp = registry.mcps["fixture-mcp"]

    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(PRE_EXISTING_SETTINGS, encoding="utf-8")
    env_dir = tmp_path / ".claude-kit" / "env.d"

    install_script_component(
        "mcps", "fixture-mcp", mcp, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )
    remove_script_component("mcps", "fixture-mcp", CATALOG_DIR, settings_path, env_dir)

    after = settings_path.read_text(encoding="utf-8")
    parsed = json.loads(after)

    assert '"theme":   "dark",' in after
    assert '"featureFlags": ["a", "b", "c"]' in after
    assert "fixture-mcp" not in parsed["mcpServers"]
    assert parsed["mcpServers"]["some-other-server"] == {"command": "foo", "args": ["bar"]}
