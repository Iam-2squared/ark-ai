"""Mixed synthetic DAG restarts preserve UNKNOWN and independent outcomes.

All four SQLite stores are disposable, separately committed and non-atomic.
A mock SUCCEEDED status is never an external side-effect receipt or replay
permission. No backend, clock attestation, or user consent is exercised.
"""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic crash matrix cannot call a backend")


def _fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    calls = {
        "root": ToolCall("writer", "mock.write", "offline", {"name": "root"}),
        "read": ToolCall("reader", "mock.read", "offline"),
        "dependent": ToolCall("writer", "mock.write", "offline", {"name": "dependent"}),
        "independent": ToolCall("writer", "mock.write", "offline", {"name": "independent"}),
    }
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("root", calls["root"]),
        PlanStep("bridge", calls["read"], ("root",)),
        PlanStep("dependent", calls["dependent"], ("bridge",)),
        PlanStep("independent", calls["independent"]),
    ))
    ledger = SyntheticOccurrenceStore(root / "occurrence.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "fixture", backend),
        ToolRegistration("reader", "mock.read", Effect.READ, "fixture", backend),
    ))
    return journal, ledger, audit, links, registry, calls, backend


def _cycle(state, name, *, now=10, fault=None):
    journal, ledger, audit, links, registry, calls, _backend = state
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, calls[name],
        OneShotAuthorization("synthetic-" + name, calls[name].request_id, 1000),
        step_id=name,
        occurrence_id="occ_" + ("1" if name == "root" else "2") * 64,
        now_ms=now, fault_at=fault, link_store=links,
    )


def _review(state, **kwargs):
    journal, ledger, audit, links, registry, _calls, backend = state
    result = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links, **kwargs,
    )
    assert backend.calls == 0
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    return result


def _retain(result):
    evidence = result.steps[0]
    return dict(
        retained_plan=evidence.plan_tail,
        retained_ledger=evidence.ledger_witness,
        retained_audit=evidence.audit_witness,
        retained_link=evidence.link_witness,
    )


def _mixed(state):
    with pytest.raises(SyntheticMockCrashInjected, match="after audit link"):
        _cycle(state, "root", fault="after_audit_link")
    mock = _cycle(state, "independent", now=12)
    assert not mock.external_outcome_known
    return mock


def test_independent_mock_success_does_not_resolve_upstream_unknown(tmp_path):
    state = _fixture(tmp_path)
    _mixed(state)
    result = _review(state)
    assert result.uncertain_step_ids == ("independent", "root")
    assert result.downstream_write_hold_step_ids == ("dependent",)
    assert result.terminally_blocked_write_step_ids == ()
    assert len(result.steps) == 3
    assert result.steps[0].link_witness.event_count == 2
    assert state[0].recover().ambiguous_running_steps == ("root",)

    reopened = _fixture(tmp_path)
    assert _review(reopened, **_retain(result)) == result
    for name in ("root", "independent"):
        with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
            _cycle(reopened, name, now=20)
    assert reopened[1].count_synthetic() == 2
    assert reopened[6].calls == 0


def test_unknown_prerequisite_cannot_start_dependent_write_after_restart(tmp_path):
    state = _fixture(tmp_path)
    _mixed(state)
    reopened = _fixture(tmp_path)
    count_before = reopened[1].count_synthetic()
    with pytest.raises(PlanConflictError, match="dependencies"):
        _cycle(reopened, "dependent", now=20)
    assert reopened[1].count_synthetic() == count_before
    assert reopened[0].recover().ambiguous_running_steps == ("root",)
    assert _review(reopened).downstream_write_hold_step_ids == ("dependent",)
    assert reopened[6].calls == 0


def test_terminal_failure_preserves_unknown_receipt_and_blocks_descendants(tmp_path):
    state = _fixture(tmp_path)
    _mixed(state)
    state[0].append("root", StepState.FAILED, expected_revision=1, at_ms=20)
    result = _review(state)
    statuses = dict(
        (name, status) for name, status, _revision
        in state[0].recover().step_statuses
    )
    assert statuses == {
        "bridge": "blocked", "dependent": "blocked",
        "independent": "succeeded", "root": "failed",
    }
    # A FAILED local journal status cannot erase separately committed
    # occurrence/audit/link evidence or establish an external outcome.
    assert result.uncertain_step_ids == ("independent", "root")
    assert result.terminally_blocked_write_step_ids == ("dependent",)
    assert result.downstream_write_hold_step_ids == ("dependent",)

    reopened = _fixture(tmp_path)
    assert _review(reopened, **_retain(result)) == result
    assert reopened[6].calls == 0
