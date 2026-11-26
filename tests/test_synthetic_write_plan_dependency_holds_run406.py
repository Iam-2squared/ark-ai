"""Transitive dependency holds are diagnoses, never dispatch or replay grants.

All stores are disposable local SQLite fixtures and every backend refuses calls.
"""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic diagnosis must never dispatch")


def _fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    backend = NoBackend()
    calls = (
        ToolCall("writer", "mock.write", "local", {"step": "alpha"}),
        ToolCall("reader", "mock.read", "local"),
        ToolCall("writer", "mock.write", "local", {"step": "omega"}),
        ToolCall("writer", "mock.write", "local", {"step": "independent"}),
    )
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("alpha", calls[0]),
        PlanStep("bridge", calls[1], ("alpha",)),
        PlanStep("omega", calls[2], ("bridge",)),
        PlanStep("independent", calls[3]),
    ))
    path = root / "occ.sqlite"
    ledger = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "synthetic", backend),
        ToolRegistration("reader", "mock.read", Effect.READ, "synthetic", backend),
    ))
    return journal, path, audit, registry, backend, ledger, calls


def _review(state):
    result = review_synthetic_write_plan(*state[:4])
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    assert state[4].calls == 0
    return result


def test_unstarted_plan_has_no_direct_or_dependency_holds(tmp_path):
    result = _review(_fixture(tmp_path))
    assert result.uncertain_step_ids == ()
    assert result.downstream_write_hold_step_ids == ()
    assert result.terminally_blocked_write_step_ids == ()


def test_unknown_running_write_holds_transitive_write_across_read_bridge(tmp_path):
    state = _fixture(tmp_path)
    state[0].append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    result = _review(state)
    assert result.uncertain_step_ids == ("alpha",)
    assert result.downstream_write_hold_step_ids == ("omega",)
    assert result.terminally_blocked_write_step_ids == ()
    assert _review(_fixture(tmp_path)) == result


def test_terminal_failed_write_holds_transitive_descendant(tmp_path):
    state = _fixture(tmp_path)
    state[0].append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    state[0].append("alpha", StepState.FAILED, expected_revision=1, at_ms=12)
    result = _review(state)
    assert result.uncertain_step_ids == ()
    assert result.downstream_write_hold_step_ids == ()
    assert result.terminally_blocked_write_step_ids == ("omega",)


@pytest.mark.parametrize("terminal", (StepState.BLOCKED, StepState.CANCELLED))
def test_pending_write_terminal_state_holds_descendants(tmp_path, terminal):
    state = _fixture(tmp_path)
    state[0].append("alpha", terminal, expected_revision=0, at_ms=10)
    result = _review(state)
    assert result.terminally_blocked_write_step_ids == ("omega",)
    assert result.downstream_write_hold_step_ids == ()


def test_terminal_read_bridge_holds_downstream_write(tmp_path):
    state = _fixture(tmp_path)
    state[0].append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    state[0].append("alpha", StepState.SUCCEEDED, expected_revision=1, at_ms=12)
    state[0].append("bridge", StepState.RUNNING, expected_revision=0, at_ms=13)
    state[0].append("bridge", StepState.FAILED, expected_revision=1, at_ms=14)
    result = _review(state)
    assert result.uncertain_step_ids == ()
    assert result.terminally_blocked_write_step_ids == ("omega",)


def test_uncertain_independent_write_has_no_downstream_hold(tmp_path):
    state = _fixture(tmp_path)
    state[0].append("independent", StepState.RUNNING, expected_revision=0, at_ms=10)
    result = _review(state)
    assert result.uncertain_step_ids == ("independent",)
    assert result.downstream_write_hold_step_ids == ()
    assert result.terminally_blocked_write_step_ids == ()


def test_direct_uncertain_descendant_is_not_double_counted_as_downstream(tmp_path):
    state = _fixture(tmp_path)
    state[0].append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    call = state[6][2]
    state[5].reserve_synthetic(
        state[3], call,
        OneShotAuthorization("disconnected", call.request_id, 1000),
        occurrence_id="occ_" + "d" * 64, now_ms=11,
    )
    result = _review(state)
    assert result.uncertain_step_ids == ("alpha", "omega")
    assert result.downstream_write_hold_step_ids == ()
    assert result.terminally_blocked_write_step_ids == ()
