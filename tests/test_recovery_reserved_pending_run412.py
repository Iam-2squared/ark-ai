"""Archived PENDING-with-reservation WRITE cannot become a known external result."""

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
from ark.agency.synthetic_recovery_archive_review import (
    SyntheticRecoveryArchiveRejected,
    archive_synthetic_recovery,
    recheck_synthetic_recovery_archive,
)
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class NeverExecute:
    def execute(self, call):
        raise AssertionError("archived synthetic recovery must not dispatch")


def _fixture(tmp_path, *, reserved):
    call = ToolCall("offline", "mock.write", "local", {"fixture": "pending"})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("write", call),),
    )
    ledger_path = tmp_path / "ledger.sqlite"
    ledger = SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "mock.write", Effect.WRITE, "inert", NeverExecute(),
        ),
    ))
    if reserved:
        ledger.reserve_synthetic(
            registry, call,
            OneShotAuthorization("local-only", call.request_id, 1000),
            occurrence_id="occ_" + "a" * 64, now_ms=11,
        )
    captured = review_synthetic_write_recovery(
        journal, ledger_path, audit, registry, call, step_id="write",
    )
    archive = archive_synthetic_recovery(captured)
    return archive, journal, ledger_path, audit, registry, call


def _recheck(state):
    archive, journal, path, audit, registry, call = state
    return recheck_synthetic_recovery_archive(
        archive, journal, path, audit, registry, call,
    )


@pytest.mark.parametrize("terminal", (StepState.SUCCEEDED, StepState.FAILED))
def test_retained_pending_reservation_refuses_later_local_terminal_verdict(
    tmp_path, terminal,
):
    state = _fixture(tmp_path, reserved=True)
    state[1].append("write", StepState.RUNNING, expected_revision=0, at_ms=15)
    state[1].append("write", terminal, expected_revision=1, at_ms=16)
    with pytest.raises(
        SyntheticRecoveryArchiveRejected,
        match="archived reserved PENDING WRITE",
    ):
        _recheck(state)


def test_unchanged_pending_reservation_is_inert_and_retained(tmp_path):
    state = _fixture(tmp_path, reserved=True)
    review = _recheck(state)
    assert review.step_state == "pending"
    assert len(review.matching_occurrences) == 1
    assert review.ambiguous_write is False
    assert not review.dispatch_authorized
    assert not review.external_outcome_known
    assert not review.automatic_replay_authorized


def test_pending_without_reservation_never_receives_external_authority(tmp_path):
    state = _fixture(tmp_path, reserved=False)
    state[1].append("write", StepState.RUNNING, expected_revision=0, at_ms=15)
    next_review = _recheck(state)
    assert next_review.ambiguous_write is True
    assert next_review.step_state == "running"
    assert not next_review.external_outcome_known
    assert not next_review.automatic_replay_authorized
