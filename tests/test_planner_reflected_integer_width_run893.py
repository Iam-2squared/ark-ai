"""Planner rejects reflected unbounded integers before canonical hashing.

The frozen ToolCall constructor is unchanged; these checks protect only the
standalone disconnected PlanGraph from a replaced post-init JSON carrier.
"""

from types import MappingProxyType

import pytest

from ark.agency import contracts
from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


def _reflected(value: object) -> PlanStep:
    call = ToolCall(
        "offline.inspect", "fixture.read", "synthetic", {"safe": 1},
    )
    object.__setattr__(
        call, "arguments", MappingProxyType({"reflected": value}),
    )
    return PlanStep("step", call)


@pytest.mark.parametrize(
    "replacement",
    (
        1 << 20_000,
        -(1 << 20_000),
        MappingProxyType({"nested": 1 << 20_000}),
    ),
    ids=("positive-oversize", "negative-oversize", "nested-oversize"),
)
def test_oversized_reflected_integer_is_denied_before_json_callback(
    replacement, monkeypatch,
):
    def forbidden_hash(_value):
        raise AssertionError("private reflected JSON reached the digest callback")

    # Construct the valid ToolCall BEFORE replacing its hash boundary.
    # The injector is only meant to prove PlanGraph denies reflected values.
    step = _reflected(replacement)
    monkeypatch.setattr(contracts, "_canonical_json", forbidden_hash)
    with pytest.raises(PlanConflictError, match="carrier changed"):
        PlanGraph((step,))


def test_bounded_reflected_integer_remains_usable_in_read_only_plan():
    # Exactly 14,000 bits, safely below the default Python JSON digit limit.
    value = 1 << 13_999
    assert value.bit_length() == 14_000
    graph = PlanGraph((_reflected(value),))
    assert graph.topology_digest().startswith("plan_")
    assert tuple(graph.ready_steps())[0].step_id == "step"


def test_original_nested_normal_json_int_preserves_canonical_request_digest():
    call = ToolCall(
        "offline.inspect", "fixture.read", "synthetic",
        {"nested": {"n": 1 << 12_000}},
    )
    initial = call.request_id
    graph = PlanGraph((PlanStep("step", call),))
    assert graph.steps["step"].call.request_id == initial
    assert graph.topology_digest().startswith("plan_")
