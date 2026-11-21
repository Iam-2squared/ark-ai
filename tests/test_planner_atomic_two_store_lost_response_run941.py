"""Two disconnected journals remain manual-only after lost child responses.

A synthetic child persists both a Planner RUNNING transition and a local
pre-action reservation, then dies without returning a receipt. The ordering
is deliberately reversed across cases. This DOES NOT provide a cross-store
transaction, independent custody, consent or real external exactly-once work.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "synthetic-step",
            ToolCall("fixture.offline", "fixture.write", "private", {"id": 1}),
        ),
    )


def _claim() -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)


def _write_then_exit(planner_path: str, audit_path: str, order: str) -> None:
    def record_plan() -> None:
        journal = SyntheticPlanJournal(Path(planner_path), _steps())
        genesis = journal.recover().tail
        result = journal.append(
            "synthetic-step", StepState.RUNNING,
            expected_revision=0, at_ms=10, retained=genesis,
        )
        assert result.dispatch_authorized is False
        assert result.automatic_replay_authorized is False

    def record_preaction() -> None:
        ledger = DisconnectedAtomicPreactionLedger(Path(audit_path))
        ledger.reserve(_claim(), retained=genesis_atomic_preaction_witness())

    if order == "plan-first":
        record_plan()
        record_preaction()
    else:
        assert order == "preaction-first"
        record_preaction()
        record_plan()
    # Deliberately no reply/receipt from a potentially already-committed child.
    os._exit(0)


@pytest.mark.parametrize("order", ("plan-first", "preaction-first"))
def test_two_store_postcommit_lost_response_does_not_grant_replay(
    tmp_path: Path, order: str,
) -> None:
    planner_path = tmp_path / "synthetic-plan.sqlite3"
    preaction_path = tmp_path / "synthetic-preaction.sqlite3"
    retained_plan = SyntheticPlanJournal(planner_path, _steps()).recover().tail
    DisconnectedAtomicPreactionLedger.create(preaction_path)
    retained_preaction = genesis_atomic_preaction_witness()
    child = get_context("spawn").Process(
        target=_write_then_exit,
        args=(str(planner_path), str(preaction_path), order),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    # Neither store is a receipt of the other's COMMIT. An unknown external
    # effect remains unknown even when both local records are present.
    for _ in range(2):
        plan = SyntheticPlanJournal(planner_path, _steps()).recover(
            retained=retained_plan,
        )
        review = review_atomic_unknown_outcome(
            DisconnectedAtomicPreactionLedger(preaction_path),
            retained_preaction,
            _claim(),
        )
        assert plan.ambiguous_running_steps == ("synthetic-step",)
        assert dict(
            (name, (state, revision))
            for name, state, revision in plan.step_statuses
        )["synthetic-step"] == ("running", 1)
        assert plan.dispatch_authorized is False
        assert plan.automatic_replay_authorized is False
        assert review.local_state == "LOCALLY_RECORDED"
        assert review.locally_present is True
        assert review.manual_review_required is True
        assert review.dispatch_authorized is False
        assert review.automatic_replay_authorized is False
        assert review.external_effect_verified is False
        assert review.independent_custody_verified is False
