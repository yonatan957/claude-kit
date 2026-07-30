"""Unit tests for core.pending and core.submit (T012).

Covers newly_installed vs. user_requested_reconfigure reasons, masked-input
metadata, and FR-014 (a failed verify leaves the component PENDING_CONFIGURATION
with its install untouched).
"""

import json

from src.core.configure import SubmitContext, pending, submit


def _registry():
    return {
        "mcps": {
            "jira-internal": {
                "description": "Internal Jira access",
                "inputs": [
                    {"name": "JIRA_API_TOKEN", "prompt": "Paste your Jira API token", "sensitive": True}
                ],
            }
        }
    }


def test_pending_returns_newly_installed_components_awaiting_config():
    state = {"mcps": {"jira-internal": {"source": "claude-kit", "config": {"status": "pending"}}}}
    steps = pending(state, _registry())

    assert len(steps) == 1
    step = steps[0]
    assert step.component.name == "jira-internal"
    assert step.reason == "newly_installed"
    assert step.inputs[0].name == "JIRA_API_TOKEN"
    assert step.inputs[0].sensitive is True


def test_pending_marks_reconfigure_reason_when_previously_verified():
    state = {
        "mcps": {
            "jira-internal": {
                "source": "claude-kit",
                "config": {"status": "pending", "verified_at": "2026-07-10T09:14:03Z"},
            }
        }
    }
    steps = pending(state, _registry())
    assert steps[0].reason == "user_requested_reconfigure"


def test_pending_skips_already_configured_and_not_installed():
    state = {"mcps": {"jira-internal": {"source": "claude-kit", "config": {"status": "done"}}}}
    assert pending(state, _registry()) == []


def _ctx(tmp_path, installed, run_config=None, run_verify=None):
    installed_path = tmp_path / "installed.json"
    installed_path.write_text(json.dumps(installed), encoding="utf-8")
    kwargs = {}
    if run_config is not None:
        kwargs["run_config"] = run_config
    if run_verify is not None:
        kwargs["run_verify"] = run_verify
    return SubmitContext(installed_path=installed_path, installed=installed, registry=_registry(), **kwargs)


def test_submit_success_marks_component_done_and_verified(tmp_path):
    installed = {"mcps": {"jira-internal": {"source": "claude-kit", "config": {"status": "pending"}}}}
    ctx = _ctx(
        tmp_path,
        installed,
        run_config=lambda step, answers, entry: (True, None),
        run_verify=lambda step, entry: (True, None),
    )
    steps = pending(installed, _registry())

    result = submit(steps[0], {"JIRA_API_TOKEN": "abc123"}, ctx)

    assert result.ok is True
    assert result.verified is True
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert on_disk["mcps"]["jira-internal"]["config"]["status"] == "done"
    assert "verified_at" in on_disk["mcps"]["jira-internal"]["config"]


def test_submit_failure_leaves_component_pending_and_install_untouched(tmp_path):
    installed = {"mcps": {"jira-internal": {"source": "claude-kit", "config": {"status": "pending"}}}}
    ctx = _ctx(
        tmp_path,
        installed,
        run_config=lambda step, answers, entry: (True, None),
        run_verify=lambda step, entry: (False, "MCP did not respond"),
    )
    steps = pending(installed, _registry())

    result = submit(steps[0], {"JIRA_API_TOKEN": "wrong-token"}, ctx)

    assert result.ok is False
    assert result.verified is False
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    # component's install is untouched — still present with source claude-kit — only config stays pending
    assert on_disk["mcps"]["jira-internal"]["source"] == "claude-kit"
    assert on_disk["mcps"]["jira-internal"]["config"]["status"] == "pending"


def test_submit_config_script_failure_also_leaves_component_pending(tmp_path):
    installed = {"mcps": {"jira-internal": {"source": "claude-kit", "config": {"status": "pending"}}}}
    ctx = _ctx(
        tmp_path,
        installed,
        run_config=lambda step, answers, entry: (False, "config.sh exited 1"),
    )
    steps = pending(installed, _registry())

    result = submit(steps[0], {"JIRA_API_TOKEN": "abc123"}, ctx)

    assert result.ok is False
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert on_disk["mcps"]["jira-internal"]["source"] == "claude-kit"
    assert on_disk["mcps"]["jira-internal"]["config"]["status"] == "pending"
