"""Transition ingress rejects unbounded or ill-formed step IDs before lookup.

All actions are synthetic PlanGraph state transitions; no ToolBackend runs.
The constructor's UTF-8 and size limits also apply to later transition IDs.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _graph(step_id="first"):
    return PlanGraph((
        PlanStep(step_id, ToolCall("offline.inspect", "fixture.read", "synthetic", {})),
    ))


@pytest.mark.parametrize(
    ("invalid", "message"),
    [
        ("x" * 4097, "budget"),
        ("\ud800", "UTF-8"),
        ("あ" * 1366, "budget"),
    ],
)
def test_transition_refuses_unbounded_or_invalid_unicode_before_state_lookup(
    invalid, message,
):
    graph = _graph()
    prior = graph.status_digest()
    with pytest.raises(PlanConflictError, match=message):
        graph.transition(invalid, StepState.RUNNING, expected_revision=0)
    assert graph.status_digest() == prior
    assert graph.statuses()["first"].revision == 0


class _TrapString(str):
    def __hash__(self):
        raise AssertionError("str subclass __hash__ must never run")


def test_transition_rejects_subclass_without_hashing():
    graph = _graph()
    with pytest.raises(TypeError, match="exact string"):
        graph.transition(_TrapString("first"), StepState.RUNNING, expected_revision=0)
    assert graph.statuses()["first"].state is StepState.PENDING


def test_transition_allows_maximum_valid_utf8_step_id():
    # 1365 three-byte characters plus one ASCII byte is exactly 4096 UTF-8 bytes.
    step_id = "あ" * 1365 + "x"
    assert len(step_id.encode("utf-8")) == 4096
    graph = _graph(step_id)
    status = graph.transition(step_id, StepState.RUNNING, expected_revision=0)
    assert status.state is StepState.RUNNING
    assert status.revision == 1
    assert graph.statuses()[step_id].state is StepState.RUNNING
