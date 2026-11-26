"""Registry-bound cross-store recovery must not rebind an equivalent impostor.

All reviewers are disconnected: a synthetic receipt is never WRITE authority.
"""

import pytest

import ark.agency.synthetic_recovery_triage as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, call):
        raise AssertionError("cross-store recovery must not dispatch tools")


def _fixture(tmp_path):
    call = ToolCall("offline", "fixture.write", "local", {"task": 11})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("write", call),),
    )
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    registry = ToolRegistry((
        ToolRegistration("offline", "fixture.write", Effect.WRITE, "mock", NeverBackend()),
    ))
    return journal, ledger, audit, registry, call


def _review(state):
    journal, ledger, audit, registry, call = state
    return module.review_synthetic_write_recovery(
        journal, ledger, audit, registry, call, step_id="write",
    )


@pytest.mark.parametrize("impostor", ("equal_call", "cloned_registration", "revision"))
def test_first_binding_must_match_exact_original_subject(
    tmp_path, monkeypatch, impostor,
):
    state = _fixture(tmp_path)
    original = ToolRegistry.bind

    def swapped(self, call):
        bound = original(self, call)
        if impostor == "equal_call":
            impostor_call = ToolCall(
                call.tool, call.capability, call.scope, dict(call.arguments),
            )
            assert impostor_call is not call
            assert impostor_call.request_id == call.request_id
            return BoundAction(
                bound.registry_revision, impostor_call,
                bound.registration, bound.bound_action_id,
            )
        if impostor == "cloned_registration":
            registration = bound.registration
            clone = ToolRegistration(
                registration.name, registration.capability,
                registration.effect, registration.backend_id,
                registration.backend,
            )
            assert clone == registration and clone is not registration
            return BoundAction(
                bound.registry_revision, call, clone, bound.bound_action_id,
            )
        return BoundAction(
            "tools_" + "f" * 64, call,
            bound.registration, bound.bound_action_id,
        )

    monkeypatch.setattr(ToolRegistry, "bind", swapped)
    with pytest.raises(
        module.SyntheticRecoveryRejected, match="binding subject changed",
    ):
        _review(state)


def test_second_binding_cannot_replace_original_action(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    original = ToolRegistry.bind
    seen = []

    def swapped(self, call):
        seen.append(call.request_id)
        result = original(self, call)
        if len(seen) == 2:
            cloned = ToolCall(
                call.tool, call.capability, call.scope, dict(call.arguments),
            )
            return BoundAction(
                result.registry_revision, cloned,
                result.registration, result.bound_action_id,
            )
        return result

    monkeypatch.setattr(ToolRegistry, "bind", swapped)
    with pytest.raises(
        module.SyntheticRecoveryRejected, match="registry or action changed",
    ):
        _review(state)
    assert len(seen) == 2


def test_valid_original_binding_remains_inert(tmp_path):
    state = _fixture(tmp_path)
    reviewed = _review(state)
    assert reviewed.step_id == "write"
    assert reviewed.step_state == "pending"
    assert not reviewed.dispatch_authorized
    assert not reviewed.automatic_replay_authorized
    assert not reviewed.external_outcome_known
