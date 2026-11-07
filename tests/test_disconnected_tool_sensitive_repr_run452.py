"""Detached tool fixtures must never dump caller-provided JSON via repr.

These tests protect accidental diagnostics only. Explicit access/asdict still
exposes the underlying sensitive data, and no real execution is authorized.
"""

from dataclasses import asdict, fields

import pytest

from ark.agency.disconnected_batch_plan import DisconnectedBatchPlan, DisconnectedBatchStep
from ark.agency.disconnected_reference_binding import (
    SyntheticBoundArguments,
    SyntheticReadResult,
)
from ark.agency.disconnected_result_budget import DetachedReadResult
from ark.agency.disconnected_toolbox import DisconnectedToolRequest, DisconnectedToolResult

_SECRET = '{"user_text":"private_tool_payload_run452"}'
_SHA = "a" * 64


@pytest.mark.parametrize(
    ("cls", "name"),
    [
        (DisconnectedToolRequest, "canonical_args_json"),
        (DisconnectedToolResult, "canonical_result_json"),
        (DisconnectedBatchStep, "canonical_args_json"),
        (DisconnectedBatchPlan, "canonical_plan_json"),
        (DetachedReadResult, "canonical_result_json"),
        (SyntheticReadResult, "canonical_result_json"),
        (SyntheticBoundArguments, "canonical_args_json"),
    ],
)
def test_private_json_is_not_part_of_dataclass_repr(cls, name):
    assert next(item for item in fields(cls) if item.name == name).repr is False


def test_detached_tool_input_and_result_are_hidden_without_losing_values():
    request = DisconnectedToolRequest("req_" + "0" * 32, "text.find", _SECRET)
    result = DisconnectedToolResult(request.request_id, "text.find", _SHA, _SECRET, _SHA)
    assert _SECRET not in repr(request)
    assert _SECRET not in repr(result)
    assert request.canonical_args_json == _SECRET
    assert result.canonical_result_json == _SECRET
    assert asdict(request)["canonical_args_json"] == _SECRET
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_detached_batch_nested_step_cannot_reveal_untrusted_arguments():
    step = DisconnectedBatchStep("step_" + "0" * 16, "text.stats", _SECRET)
    batch = DisconnectedBatchPlan("req_" + "0" * 32, (step,), _SECRET, _SHA)
    assert _SECRET not in repr(step)
    assert _SECRET not in repr(batch)
    assert batch.canonical_plan_json == _SECRET
    assert batch.steps[0].canonical_args_json == _SECRET
    assert batch.write_authorized is False


def test_detached_result_and_reference_binding_cannot_dump_result_json():
    result = DetachedReadResult("step_" + "0" * 16, "text.find", _SECRET, _SHA)
    reference = SyntheticReadResult("step_" + "0" * 16, _SECRET, _SHA)
    bound = SyntheticBoundArguments("req_" + "0" * 32, ("step_" + "0" * 16,), _SECRET, _SHA)
    for value in (result, reference, bound):
        assert _SECRET not in repr(value)
    assert result.canonical_result_json == _SECRET
    assert reference.canonical_result_json == _SECRET
    assert bound.canonical_args_json == _SECRET
    assert bound.dispatch_authorized is False
    assert bound.source_authenticated is False
