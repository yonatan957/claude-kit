"""Unit tests: src/installers/content.py and src/installers/script.py must
produce no duplicate entries/files/registrations when install or remove is
run twice consecutively (Principle IV / FR-037)."""

import json
from pathlib import Path

import pytest

from src.core.state_model import Registry
from src.installers.content import install_content, remove_content
from src.installers.script import install_script_component, remove_script_component

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "registry_repo" / "registry.json"
CATALOG_DIR = (REPO_ROOT / "tests" / "fixtures" / "registry_repo").resolve()


@pytest.fixture
def registry() -> Registry:
    return Registry.model_validate(json.loads(FIXTURE_REGISTRY.read_text(encoding="utf-8")))


def test_content_install_twice_is_stable_and_not_duplicated(tmp_path, registry):
    component = registry.skills["fixture-skill"]
    target = tmp_path / "skills"
    target.mkdir()

    first = install_content("skills", "fixture-skill", component, CATALOG_DIR, target)
    second = install_content("skills", "fixture-skill", component, CATALOG_DIR, target)

    assert first.installed_hash == second.installed_hash
    files = list((target / "fixture-skill").iterdir())
    assert len(files) == 1  # no duplicate copies


def test_content_remove_twice_is_a_no_op(tmp_path, registry):
    component = registry.skills["fixture-skill"]
    target = tmp_path / "skills"
    target.mkdir()
    install_content("skills", "fixture-skill", component, CATALOG_DIR, target)

    remove_content(component, target)
    remove_content(component, target)  # must not raise

    assert not (target / "fixture-skill").exists()


def test_script_install_twice_does_not_duplicate_mcp_registration(tmp_path, registry):
    component = registry.mcps["fixture-mcp"]
    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"

    install_script_component(
        "mcps", "fixture-mcp", component, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )
    install_script_component(
        "mcps", "fixture-mcp", component, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert list(settings["mcpServers"].keys()) == ["fixture-mcp"]


def test_script_install_twice_does_not_duplicate_secret_file(tmp_path, registry):
    component = registry.mcps["fixture-mcp"]
    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"

    install_script_component(
        "mcps", "fixture-mcp", component, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )
    install_script_component(
        "mcps", "fixture-mcp", component, CATALOG_DIR, {"api_key": "v2"}, settings_path, env_dir
    )

    secret_files = list(env_dir.iterdir())
    assert len(secret_files) == 1
    assert "v2" in secret_files[0].read_text(encoding="utf-8")


def test_script_remove_twice_is_a_no_op(tmp_path, registry):
    component = registry.mcps["fixture-mcp"]
    settings_path = tmp_path / ".claude" / "settings.json"
    env_dir = tmp_path / ".claude-kit" / "env.d"
    install_script_component(
        "mcps", "fixture-mcp", component, CATALOG_DIR, {"api_key": "v1"}, settings_path, env_dir
    )

    remove_script_component("mcps", "fixture-mcp", CATALOG_DIR, settings_path, env_dir)
    remove_script_component("mcps", "fixture-mcp", CATALOG_DIR, settings_path, env_dir)  # no-op

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "fixture-mcp" not in settings["mcpServers"]
    assert not env_dir.exists() or not list(env_dir.iterdir())
