"""NUL-bearing Planner identities must fail before DAG/hash admission.

No frozen dataclass contract, backend implementation or tool execution is
changed by these disconnected regression cases.
"""

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, ToolCall


@pytest.mark.parametrize(
    "field",
    ("step_id", "depends_on", "tool", "capability", "scope"),
)
def test_reflected_embedded_nul_denied_at_graph_boundary(field: str) -> None:
    call = ToolCall("fixture.read", "read", "offline", {"value": 1})
    step = PlanStep("root", call)
    label = "safe\x00unsafe"
    if field == "depends_on":
        object.__setattr__(step, field, (label,))
    elif field == "step_id":
        object.__setattr__(step, field, label)
    else:
        object.__setattr__(call, field, label)
    with pytest.raises(PlanConflictError, match="NUL separator"):
        PlanGraph((step,))


def test_constructor_accepted_nul_cannot_enter_plan_graph() -> None:
    # Keep the frozen constructor unchanged: Planner ingress is stricter.
    step = PlanStep("root\x00suffix", ToolCall("fixture", "read", "offline"))
    with pytest.raises(PlanConflictError, match="NUL separator"):
        PlanGraph((step,))


def test_normal_unicode_labels_preserve_disconnected_plan_readiness() -> None:
    call = ToolCall("fixture.read", "read", "ローカル")
    graph = PlanGraph((PlanStep("準備", call),))
    assert [step.step_id for step in graph.ready_steps()] == ["準備"]
    assert graph.topology_digest().startswith("plan_")
