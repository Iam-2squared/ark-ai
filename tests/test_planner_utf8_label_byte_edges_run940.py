"""Standalone non-dispatch Planner graph labels obey exact UTF-8 limits.

This does not modify frozen PlanStep/ToolCall contracts or recover a live
operation; the graph remains an inert dependency model with no backend.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


def _step(identifier: str, *dependencies: str) -> PlanStep:
    return PlanStep(
        identifier,
        ToolCall("fixture.read", "fixture.read", "local", {"fixture": True}),
        depends_on=dependencies,
    )


@pytest.mark.parametrize("location", ("step", "dependency"))
@pytest.mark.parametrize(
    ("label", "accepted"),
    (
        ("🪐" * 1024, True),   # 4,096 encoded bytes, 1,024 Python chars
        ("🪐" * 1025, False),  # 4,100 encoded bytes, below char limit
        ("a" * 4096, True),
        ("a" * 4097, False),
    ),
)
def test_plan_graph_identity_budget_applies_to_step_and_dependency_labels(
    location: str, label: str, accepted: bool,
) -> None:
    if location == "step":
        steps = (_step(label),)
    else:
        steps = (_step(label), _step("child", label))

    if not accepted:
        with pytest.raises(PlanConflictError, match="budget exceeded"):
            PlanGraph(steps)
        return
    graph = PlanGraph(steps)
    assert graph.topology_digest().startswith("plan_")
    assert tuple(step.step_id for step in graph.ready_steps()) == (label,)
    assert graph.statuses()[label].revision == 0


@pytest.mark.parametrize("label", ("🪐" * 1025, "a" * 4097))
def test_reflectively_replaced_step_identity_does_not_bypass_graph_admission(
    label: str,
) -> None:
    original = _step("safe-step")
    object.__setattr__(original, "step_id", label)
    with pytest.raises(PlanConflictError, match="budget exceeded"):
        PlanGraph((original,))
