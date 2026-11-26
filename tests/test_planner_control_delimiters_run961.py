"""Run961: opt-in Planner ingress refuses ambiguous control-bearing identities.

The frozen ToolCall and PlanStep constructors are deliberately unchanged.
No tool backend, filesystem action or authorization is invoked in these tests.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph

_CONTROLS = ("\n", "\r", "\t", "\x01", "\x1f", "\x7f")


@pytest.mark.parametrize("control", _CONTROLS)
@pytest.mark.parametrize(
    "field", ("step_id", "dependency", "tool", "capability", "scope"),
)
def test_planner_rejects_control_identity_before_topology_or_request_hash(
    control: str, field: str,
) -> None:
    bad = "left" + control + "right"
    call = ToolCall(
        bad if field == "tool" else "fixture.read",
        bad if field == "capability" else "fixture.read",
        bad if field == "scope" else "local-only",
    )
    steps = (
        PlanStep(
            bad if field == "step_id" else "root",
            call,
            (bad,) if field == "dependency" else (),
        ),
    )
    # The low-level dataclasses still accept these exact strings. Their
    # standalone Planner admission is the stricter optional boundary.
    with pytest.raises(PlanConflictError, match="control delimiter|NUL separator"):
        PlanGraph(steps)


@pytest.mark.parametrize("field", ("step_id", "scope"))
def test_reflectively_modified_frozen_input_is_not_admitted(field: str) -> None:
    call = ToolCall("fixture.read", "fixture.read", "local-only")
    step = PlanStep("root", call)
    if field == "step_id":
        object.__setattr__(step, "step_id", "root\ninjected")
    else:
        object.__setattr__(call, "scope", "local\rforged")
    with pytest.raises(PlanConflictError, match="control delimiter"):
        PlanGraph((step,))


def test_valid_unicode_graph_identifiers_and_dependencies_still_work() -> None:
    call = ToolCall("fixture.測定", "offline.温度", "private/東京 β")
    graph = PlanGraph((
        PlanStep("根📍", call),
        PlanStep("処理-二", call, ("根📍",)),
    ))
    assert [step.step_id for step in graph.ready_steps()] == ["根📍"]
    assert graph.topology_digest().startswith("plan_")
