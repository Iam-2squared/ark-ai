"""Run971: C1 terminal controls cannot enter standalone Planner DAG IDs.

PlanStep/ToolCall v1 input contracts remain frozen. This is a disconnected
graph review only, not execution approval or a durable recovery claim.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph

_C1 = ("\u0080", "\u0081", "\u008d", "\u0090", "\u009b", "\u009f")


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize(
    "field", ("step_id", "dependency", "tool", "capability", "scope"),
)
def test_c1_identifiers_denied_before_graph_construction(
    control: str, field: str,
) -> None:
    forged = "safe" + control + "spoof"
    call = ToolCall(
        forged if field == "tool" else "fixture.read",
        forged if field == "capability" else "fixture.read",
        forged if field == "scope" else "private",
    )
    step = PlanStep(
        forged if field == "step_id" else "root",
        call,
        (forged,) if field == "dependency" else (),
    )
    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph((step,))


@pytest.mark.parametrize("field", ("step_id", "scope"))
def test_reflected_c1_field_denied_before_graph_hash(field: str) -> None:
    call = ToolCall("fixture.read", "fixture.read", "private")
    step = PlanStep("root", call)
    if field == "step_id":
        object.__setattr__(step, "step_id", "root\u009bspoof")
    else:
        object.__setattr__(call, "scope", "private\u009fspoof")
    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph((step,))


def test_multilingual_dag_and_dependency_order_still_work() -> None:
    call = ToolCall("検索", "ローカル読取", "端末/個人")
    graph = PlanGraph((
        PlanStep("親", call),
        PlanStep("子", call, ("親",)),
    ))
    assert [step.step_id for step in graph.ready_steps()] == ["親"]
    assert graph.topology_digest().startswith("plan_")
