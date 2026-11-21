"""Planner rejects reflected nested argument carriers before callback access.

No backend is ever called. The frozen ToolCall contract is unchanged; these
tests target post-constructor reflection and the standalone PlanGraph guard.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


class _HostileMapping:
    def __init__(self, accessed: list[str]) -> None:
        self.accessed = accessed

    def items(self):
        self.accessed.append("items")
        raise AssertionError("Planner evaluated an untrusted mapping")


class _HostileSequence:
    def __init__(self, accessed: list[str]) -> None:
        self.accessed = accessed

    def __iter__(self):
        self.accessed.append("iter")
        raise AssertionError("Planner iterated an untrusted sequence")


@pytest.mark.parametrize("shape", ("nested_mapping", "nested_sequence", "huge_int"))
def test_reflected_nested_arguments_denied_before_user_callbacks(
    shape: str,
) -> None:
    accessed: list[str] = []
    if shape == "nested_mapping":
        payload = _HostileMapping(accessed)
    elif shape == "nested_sequence":
        payload = _HostileSequence(accessed)
    else:
        payload = 1 << 14_001

    call = ToolCall("fixture.read", "fixture.read", "fixture:owner", {"ok": 1})
    object.__setattr__(
        call, "arguments", MappingProxyType({"untrusted": (payload,)})
    )
    with pytest.raises(PlanConflictError, match="carrier changed before admission"):
        PlanGraph((PlanStep("step-1", call),))
    assert accessed == []


def test_original_frozen_nested_json_remains_plannable_without_dispatch() -> None:
    call = ToolCall(
        "fixture.read", "fixture.read", "fixture:owner",
        {"nested": {"numbers": [1, 2, {"ok": True}]}},
    )
    step = PlanStep("step-1", call)
    graph = PlanGraph((step,))
    assert graph.ready_steps() == (step,)
    assert graph.steps["step-1"] is step
