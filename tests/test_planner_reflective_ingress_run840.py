"""Bound Planner's in-memory admission/epoch before user-defined callbacks."""

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, ToolCall


class CallbackProbe:
    def __init__(self) -> None:
        self.events: list[str] = []

    def __hash__(self) -> int:
        self.events.append("hash")
        return hash("a")

    def __eq__(self, other: object) -> bool:
        self.events.append("eq")
        return False

    def __iter__(self):
        self.events.append("iter")
        yield "a"


def _step(name: str = "a") -> PlanStep:
    return PlanStep(name, ToolCall("probe.read", "probe.read", "local:fixture"))


@pytest.mark.parametrize("field", ["step_id", "depends_on", "call"])
def test_graph_refuses_reflected_step_carriers_before_callback(field: str) -> None:
    step = _step()
    hostile = CallbackProbe()
    replacement = (hostile,) if field == "depends_on" else hostile
    object.__setattr__(step, field, replacement)
    with pytest.raises(PlanConflictError, match="before admission"):
        PlanGraph((step,))
    assert hostile.events == []


def test_graph_refuses_duplicate_dependencies_added_after_construction() -> None:
    root = _step()
    child = PlanStep("b", root.call, ("a",))
    object.__setattr__(child, "depends_on", ("a", "a"))
    with pytest.raises(PlanConflictError, match="duplicate"):
        PlanGraph((root, child))


def test_plan_epoch_refuses_executable_record_before_iterating() -> None:
    graph = PlanGraph((_step(),))
    hostile = CallbackProbe()
    graph._step_epoch = (hostile,)
    with pytest.raises(PlanConflictError, match="plan mapping"):
        graph.ready_steps()
    assert hostile.events == []


def test_plan_epoch_refuses_executable_identifier_before_equality() -> None:
    graph = PlanGraph((_step(),))
    hostile = CallbackProbe()
    row = list(graph._step_epoch[0])
    row[0] = hostile
    graph._step_epoch = (tuple(row),)
    with pytest.raises(PlanConflictError, match="plan step input"):
        graph.ready_steps()
    assert hostile.events == []


def test_status_epoch_refuses_executable_record_before_iterating() -> None:
    graph = PlanGraph((_step(),))
    hostile = CallbackProbe()
    graph._status_epoch = (hostile,)
    with pytest.raises(PlanConflictError, match="status mapping"):
        graph.statuses()
    assert hostile.events == []


def test_status_epoch_refuses_executable_identifier_before_hash() -> None:
    graph = PlanGraph((_step(),))
    hostile = CallbackProbe()
    existing = graph._status.pop("a")
    graph._status[hostile] = existing
    hostile.events.clear()
    with pytest.raises(PlanConflictError, match="status mapping"):
        graph.statuses()
    assert hostile.events == []
