"""Standalone Planner refuses reflected identity resource exhaustion.

The frozen PlanStep/ToolCall contracts and transition semantics are not edited.
All actions here are inert tool descriptions, never executed.
"""

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, ToolCall


def _call(**changes: str) -> ToolCall:
    fields = {
        "tool": "fixture.read", "capability": "fixture.read",
        "scope": "local",
    }
    fields.update(changes)
    return ToolCall(**fields)


@pytest.mark.parametrize("field", ("step_id", "depends_on"))
@pytest.mark.parametrize("huge", ("x" * 4097, "é" * 2049))
def test_reflected_graph_identity_budget_rejects_before_graph_maps(
    field: str, huge: str,
) -> None:
    step = PlanStep("root", _call())
    object.__setattr__(
        step, field, huge if field == "step_id" else (huge,),
    )
    with pytest.raises(PlanConflictError, match="identifier budget"):
        PlanGraph((step,))


@pytest.mark.parametrize("field", ("tool", "capability", "scope"))
def test_reflected_action_label_budget_rejected_before_request_id_hash(
    field: str,
) -> None:
    step = PlanStep("root", _call())
    object.__setattr__(step.call, field, "x" * 4097)
    with pytest.raises(PlanConflictError, match="identifier budget"):
        PlanGraph((step,))


@pytest.mark.parametrize("field", ("step_id", "depends_on"))
def test_unpaired_surrogates_are_not_accepted_at_graph_boundary(
    field: str,
) -> None:
    step = PlanStep("root", _call())
    object.__setattr__(
        step, field, "bad\ud800" if field == "step_id" else ("bad\ud800",),
    )
    with pytest.raises(PlanConflictError, match="not valid UTF-8"):
        PlanGraph((step,))


def test_exact_graph_utf8_budget_retains_normal_status_transitions() -> None:
    step_id = "é" * 2048  # Exactly 4096 UTF-8 bytes.
    graph = PlanGraph((PlanStep(step_id, _call()),))
    assert graph.ready_steps()[0].step_id == step_id
    assert graph.topology_digest().startswith("plan_")


def test_excessive_dependency_edge_guard_remains_stricter_than_label_budget() -> None:
    step = PlanStep("root", _call())
    object.__setattr__(step, "depends_on", ("ok",) * 65_537)
    with pytest.raises(ValueError, match="plan dependency budget exceeded"):
        PlanGraph((step,))
