"""Registered disconnected READ evidence and Planner UNKNOWN recovery stay inert.

One synthetic fixture links registry policy and a journaled RUNNING plan after a
cold restart. None of these local reviews can execute or replay a ToolBackend.
"""

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_fixture_binding import (
    bind_disconnected_fixture_result,
)
from ark.agency.disconnected_registered_fixture_join import (
    RegisteredFixtureLinkRejected,
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("the synthetic READ must never dispatch")


def _fixtures():
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "math.sum", "fixture.read", Effect.READ, "offline-fixture", backend,
        ),
    ))
    gate = PermissionGate()
    call = ToolCall("math.sum", "fixture.read", "synthetic", {"values": [1, 2]})
    grants = (CapabilityGrant("fixture.read", "synthetic"),)
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    return backend, registry, gate, call, grants, request, result, binding


def test_cold_running_plan_and_registered_fixture_link_cannot_replay(tmp_path):
    backend, registry, gate, call, grants, req, result, binding = _fixtures()
    step = "step_" + "b" * 16
    plan_steps = (PlanStep(step, call),)
    path = tmp_path / "plan.sqlite"
    journal = SyntheticPlanJournal(path, plan_steps)
    genesis = journal.recover().tail
    running = journal.append(
        step, StepState.RUNNING, expected_revision=0, at_ms=90, retained=genesis,
    )
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, step, req, result, binding,
        observed_at_ms=100,
    )
    reopened = SyntheticPlanJournal(path, plan_steps).recover(retained=genesis)
    assert reopened.tail == running.tail
    assert reopened.ambiguous_running_steps == (step,)
    assert reopened.automatic_replay_authorized is False
    assert reopened.dispatch_authorized is False
    assert link.action_request_id == call.request_id
    assert link.fixture_request_id == req.request_id
    assert link.registry_revision == registry.revision
    assert link.backend_dispatched is False
    assert link.write_authorized is False
    assert link.replay_authorized is False
    assert link.external_result_proven is False
    assert backend.calls == 0


def test_mismatched_registered_args_deny_without_modifying_running_journal(tmp_path):
    backend, registry, gate, call, grants, req, result, binding = _fixtures()
    step = "step_" + "b" * 16
    plan_steps = (PlanStep(step, call),)
    path = tmp_path / "plan.sqlite"
    journal = SyntheticPlanJournal(path, plan_steps)
    journal.append(step, StepState.RUNNING, expected_revision=0, at_ms=90)
    tail_before = journal.recover().tail
    different = ToolCall(
        "math.sum", "fixture.read", "synthetic", {"values": [1, 3]},
    )
    with pytest.raises(
        RegisteredFixtureLinkRejected,
        match="registered arguments do not match",
    ):
        review_registered_disconnected_fixture(
            registry, gate, different, grants, step, req, result, binding,
            observed_at_ms=100,
        )
    assert SyntheticPlanJournal(path, plan_steps).recover().tail == tail_before
    assert backend.calls == 0
