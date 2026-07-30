"""Contract test: core.plan / core.apply / core.pending / core.submit signatures and
return shapes match specs/001-config-picker-tui/contracts/core-interface.md (T014)."""

import inspect
import json

from src.core.apply import ApplyContext, apply
from src.core.configure import SubmitContext, pending, request_reconfigure, submit
from src.core.models import ApplyResult, ConfigStep, SelectionPlan, VerifyResult
from src.core.plan import plan


def test_plan_signature_and_output_shape():
    params = list(inspect.signature(plan).parameters)
    assert params == ["state", "registry", "selections"]

    result = plan({}, {"types": []}, selections=set())
    assert isinstance(result, SelectionPlan)
    assert hasattr(result, "is_noop")


def test_apply_signature_and_output_shape(tmp_path):
    params = list(inspect.signature(apply).parameters)
    assert params == ["plan", "registry", "ctx"]

    installed_path = tmp_path / "installed.json"
    installed_path.write_text(json.dumps({}), encoding="utf-8")
    ctx = ApplyContext(installed_path=installed_path, installed={})

    results = apply(SelectionPlan(), registry={}, ctx=ctx)
    assert results == []
    assert inspect.signature(ApplyContext).parameters.keys() >= {
        "installed_path",
        "installed",
        "install_component",
        "remove_component",
    }


def test_pending_signature_and_output_shape():
    params = list(inspect.signature(pending).parameters)
    assert params == ["state", "registry"]

    steps = pending({}, {})
    assert steps == []


def test_submit_signature_and_output_shape(tmp_path):
    params = list(inspect.signature(submit).parameters)
    assert params == ["step", "answers", "ctx"]

    assert inspect.signature(SubmitContext).parameters.keys() >= {
        "installed_path",
        "installed",
        "registry",
        "run_config",
        "run_verify",
    }


def test_request_reconfigure_signature():
    params = list(inspect.signature(request_reconfigure).parameters)
    assert params == ["state", "type_name", "name"]


def test_output_dataclasses_match_data_model():
    assert {f for f in ApplyResult.__dataclass_fields__} == {"component", "action", "ok", "detail"}
    assert {f for f in VerifyResult.__dataclass_fields__} == {"component", "ok", "verified", "detail"}
    assert {f for f in ConfigStep.__dataclass_fields__} == {"component", "inputs", "reason"}
