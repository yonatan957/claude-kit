"""Unit tests for core.plan — pure diff of selections vs. installed state.

Covers install-only, removal-only, mixed, and no-op diffs (T006).
"""

from src.core.plan import is_first_use, plan


def _registry():
    return {
        "types": [
            {"name": "skills", "handler": "content"},
            {"name": "tools", "handler": "script"},
        ],
        "skills": {
            "dr-runbooks": {"description": "DR runbooks", "recommended": True},
            "k8s-debug": {"description": "K8s debugging"},
        },
        "tools": {
            "graphify": {"description": "Graph viz", "version": "0.9.2"},
        },
    }


def _installed_with(*, dr_runbooks=False, graphify=False):
    installed = {"schema_version": 2, "skills": {}, "tools": {}}
    if dr_runbooks:
        installed["skills"]["dr-runbooks"] = {"source": "claude-kit"}
    if graphify:
        installed["tools"]["graphify"] = {"source": "claude-kit", "version": "0.9.2"}
    return installed


def test_install_only():
    state = _installed_with()
    result = plan(state, _registry(), selections={"skills:dr-runbooks"})
    assert [c.key for c in result.to_install] == ["skills:dr-runbooks"]
    assert result.to_remove == []
    assert not result.is_noop


def test_removal_only():
    state = _installed_with(dr_runbooks=True)
    result = plan(state, _registry(), selections=set())
    assert result.to_install == []
    assert [c.key for c in result.to_remove] == ["skills:dr-runbooks"]
    assert not result.is_noop


def test_mixed_install_and_removal():
    state = _installed_with(dr_runbooks=True)
    result = plan(state, _registry(), selections={"tools:graphify"})
    assert [c.key for c in result.to_install] == ["tools:graphify"]
    assert [c.key for c in result.to_remove] == ["skills:dr-runbooks"]


def test_noop_when_selections_match_installed():
    state = _installed_with(dr_runbooks=True)
    result = plan(state, _registry(), selections={"skills:dr-runbooks"})
    assert result.to_install == []
    assert result.to_remove == []
    assert result.is_noop


def test_already_pending_configuration_is_unaffected_by_selections():
    state = _installed_with(graphify=True)
    state["tools"]["gitlab-cli"] = {"source": "claude-kit", "config": {"status": "pending"}}
    registry = _registry()
    registry["tools"]["gitlab-cli"] = {"description": "GitLab CLI", "version": "1.1.0"}
    result = plan(state, registry, selections={"tools:graphify", "tools:gitlab-cli"})
    assert result.is_noop
    assert [c.key for c in result.already_pending_configuration] == ["tools:gitlab-cli"]


def test_is_first_use_true_on_empty_installed_json():
    assert is_first_use({"schema_version": 2}) is True
    assert is_first_use({"schema_version": 2, "skills": {}}) is True


def test_is_first_use_false_when_a_managed_component_exists():
    state = _installed_with(dr_runbooks=True)
    assert is_first_use(state) is False


def test_is_first_use_true_when_only_user_added_components_exist():
    state = {"schema_version": 2, "skills": {"my-notes": {"source": "user"}}}
    assert is_first_use(state) is True

