"""Unit tests for core.apply — install/removal transactions (T008).

Covers install-only, removal-only, ordering, and FR-014's batch-level guarantee:
one component's failure must not roll back a different, already-committed component.
"""

import json

from src.core.apply import ApplyContext, apply
from src.core.models import Component


def _ctx(tmp_path, installed=None, install_component=None, remove_component=None):
    installed_path = tmp_path / "installed.json"
    installed = installed if installed is not None else {}
    installed_path.write_text(json.dumps(installed), encoding="utf-8")
    kwargs = {}
    if install_component is not None:
        kwargs["install_component"] = install_component
    if remove_component is not None:
        kwargs["remove_component"] = remove_component
    return ApplyContext(installed_path=installed_path, installed=installed, **kwargs)


def _plan(to_install=(), to_remove=()):
    from src.core.models import SelectionPlan

    return SelectionPlan(to_install=list(to_install), to_remove=list(to_remove))


def test_successful_install_updates_installed_json(tmp_path):
    component = Component(type="skills", name="dr-runbooks", description="DR runbooks")
    ctx = _ctx(tmp_path)

    results = apply(_plan(to_install=[component]), registry={}, ctx=ctx)

    assert len(results) == 1
    assert results[0].ok is True
    assert results[0].action == "installed"
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert on_disk["skills"]["dr-runbooks"]["source"] == "claude-kit"


def test_successful_removal_updates_installed_json(tmp_path):
    component = Component(type="tools", name="graphify", description="Graph viz")
    ctx = _ctx(tmp_path, installed={"tools": {"graphify": {"source": "claude-kit"}}})

    results = apply(_plan(to_remove=[component]), registry={}, ctx=ctx)

    assert results[0].ok is True
    assert results[0].action == "removed"
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert "graphify" not in on_disk.get("tools", {})


def test_install_order_is_tools_then_plugins_then_the_rest(tmp_path):
    skill = Component(type="skills", name="dr-runbooks", description="")
    tool = Component(type="tools", name="graphify", description="")
    plugin = Component(type="plugins", name="org-standards", description="")
    ctx = _ctx(tmp_path)

    results = apply(_plan(to_install=[skill, tool, plugin]), registry={}, ctx=ctx)

    assert [r.component.type for r in results] == ["tools", "plugins", "skills"]


def test_one_component_install_failure_does_not_roll_back_another_already_committed(tmp_path):
    good = Component(type="tools", name="graphify", description="")
    bad = Component(type="tools", name="broken-tool", description="")

    def install_component(component, registry_entry):
        if component.name == "broken-tool":
            return False, "install.sh exited 1"
        return True, None

    ctx = _ctx(tmp_path, install_component=install_component)

    results = apply(_plan(to_install=[good, bad]), registry={}, ctx=ctx)

    result_by_name = {r.component.name: r for r in results}
    assert result_by_name["graphify"].ok is True
    assert result_by_name["broken-tool"].ok is False

    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert on_disk["tools"]["graphify"]["source"] == "claude-kit"
    assert "broken-tool" not in on_disk.get("tools", {})


def test_removal_with_no_uninstall_script_still_forgets_the_component(tmp_path):
    component = Component(type="tools", name="legacy-thing", description="")
    ctx = _ctx(tmp_path, installed={"tools": {"legacy-thing": {"source": "claude-kit"}}})

    results = apply(_plan(to_remove=[component]), registry={}, ctx=ctx)

    assert results[0].ok is True
    assert "left on PATH" in results[0].detail or "left in place" in results[0].detail
    on_disk = json.loads(ctx.installed_path.read_text(encoding="utf-8"))
    assert "legacy-thing" not in on_disk.get("tools", {})
