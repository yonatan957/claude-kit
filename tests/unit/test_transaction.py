"""Unit tests for the install/removal transaction engine (T009).

Covers snapshot -> apply -> health-check -> commit/revert, including a failure
mid-batch that must leave an earlier, already-committed transaction untouched.
"""

from src.core.transaction import atomic_write, run_transaction


def test_successful_transaction_commits(tmp_path):
    target = tmp_path / "installed.json"
    target.write_text('{"a": 1}', encoding="utf-8")

    result = run_transaction(
        paths=[target],
        apply_fn=lambda: atomic_write(target, '{"a": 2}'),
        verify_fn=lambda _: True,
    )

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == '{"a": 2}'


def test_apply_failure_reverts_to_prior_content(tmp_path):
    target = tmp_path / "installed.json"
    target.write_text('{"a": 1}', encoding="utf-8")

    def boom():
        raise RuntimeError("install.sh exited non-zero")

    result = run_transaction(paths=[target], apply_fn=boom)

    assert result.ok is False
    assert "install.sh exited non-zero" in result.detail
    assert target.read_text(encoding="utf-8") == '{"a": 1}'


def test_verify_failure_reverts_to_prior_content(tmp_path):
    target = tmp_path / "installed.json"
    target.write_text('{"a": 1}', encoding="utf-8")

    result = run_transaction(
        paths=[target],
        apply_fn=lambda: atomic_write(target, '{"a": 2}'),
        verify_fn=lambda _: False,
    )

    assert result.ok is False
    assert result.detail == "health-check failed"
    assert target.read_text(encoding="utf-8") == '{"a": 1}'


def test_new_file_created_by_apply_is_removed_on_failure(tmp_path):
    target = tmp_path / "new_settings.json"
    assert not target.exists()

    result = run_transaction(
        paths=[target],
        apply_fn=lambda: atomic_write(target, '{"mcpServers": {}}'),
        verify_fn=lambda _: False,
    )

    assert result.ok is False
    assert not target.exists()


def test_failure_mid_batch_does_not_roll_back_an_earlier_committed_transaction(tmp_path):
    """FR-014 / Constitution I at the primitive level: two independent components,
    each its own transaction. The second one failing must not touch the first."""
    component_a = tmp_path / "tool_a_state.json"
    component_a.write_text('{"installed": false}', encoding="utf-8")
    component_b = tmp_path / "tool_b_state.json"
    component_b.write_text('{"installed": false}', encoding="utf-8")

    result_a = run_transaction(
        paths=[component_a],
        apply_fn=lambda: atomic_write(component_a, '{"installed": true}'),
        verify_fn=lambda _: True,
    )
    assert result_a.ok is True
    assert component_a.read_text(encoding="utf-8") == '{"installed": true}'

    def boom():
        raise RuntimeError("verify.sh: connection refused")

    result_b = run_transaction(paths=[component_b], apply_fn=boom)
    assert result_b.ok is False

    # component_a's already-committed transaction must remain untouched
    assert component_a.read_text(encoding="utf-8") == '{"installed": true}'
    assert component_b.read_text(encoding="utf-8") == '{"installed": false}'


def test_atomic_write_creates_parent_directories(tmp_path):
    target = tmp_path / "env.d" / "jira-internal"
    atomic_write(target, "TOKEN=<set>")
    assert target.read_text(encoding="utf-8") == "TOKEN=<set>"
    assert not target.with_suffix(target.suffix + ".tmp").exists()
