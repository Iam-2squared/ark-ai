"""Nested reflected Planner JSON is rejected before canonical request hashing.

This uses inert local ToolCalls; no registry dispatch or authorization occurs.
"""

from types import MappingProxyType

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


def _reflected_plan(replacement: object) -> PlanGraph:
    call = ToolCall(
        tool="offline_math",
        capability="read",
        scope="synthetic",
        arguments={"outer": {"valid": [1, 2]}},
    )
    # Simulate post-constructor reflection that preserves only the OUTER
    # mappingproxy type. The nested payload is not a frozen JSON carrier.
    object.__setattr__(
        call, "arguments", MappingProxyType({"outer": replacement}),
    )
    return PlanGraph((PlanStep("step", call),))


@pytest.mark.parametrize(
    "bad_nested",
    [
        {"mutable": 1},
        [1, 2],
        object(),
        float("nan"),
        float("inf"),
        "x" * 65_537,
    ],
)
def test_reflected_nested_foreign_carrier_is_rejected(bad_nested):
    with pytest.raises(PlanConflictError, match="carrier changed"):
        _reflected_plan(bad_nested)


def test_reflected_callback_mapping_is_never_visited():
    class CallbackDict(dict):
        def items(self):
            raise AssertionError("untrusted nested callback was invoked")

    with pytest.raises(PlanConflictError, match="carrier changed"):
        _reflected_plan(CallbackDict({"x": 1}))


def test_constructor_frozen_nested_json_remains_usable():
    call = ToolCall(
        tool="offline_math",
        capability="read",
        scope="synthetic",
        arguments={
            "nested": {"flags": [True, None, 1.5], "value": 3},
            "empty": [],
        },
    )
    graph = PlanGraph((PlanStep("step", call),))
    assert graph.topology_digest().startswith("plan_")
    assert tuple(graph.steps) == ("step",)
