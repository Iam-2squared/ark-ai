"""Cross-store interleavings never convert local Planner/atomic evidence to authority.

Both SQLite journals are independent. Even after a locally coherent review,
their separate commits cannot prove a simultaneous state or a real WRITE.
No real tools, approval, network, or physical device is involved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.disconnected_registered_planner_atomic_triage import (
    RegisteredPlannerAtomicTriageRejected,
    review_registered_planner_atomic_triage,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry

_FIRST = "step_" + "1" * 16
_READ = "step_" + "2" * 16
_SECOND = "step_" + "3" * 16
_OCC_FIRST = "occ_" + "a" * 64
_OCC_SECOND = "occ_" + "b" * 64
_BINDINGS = ((_FIRST, _OCC_FIRST), (_SECOND, _OCC_SECOND))


class RejectDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("cross-store review is not a tool dispatcher")


def _fixture(tmp_path: Path):
    backend = RejectDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
        ToolRegistration("reader", "fixture.read", Effect.READ, "local", backend),
    ))
    steps = (
        PlanStep(_FIRST, ToolCall("writer", "fixture.write", "local", {"v": 1})),
        PlanStep(
            _READ, ToolCall("reader", "fixture.read", "local", {"q": 1}),
            (_FIRST,),
        ),
        PlanStep(_SECOND, ToolCall("writer", "fixture.write", "local", {"v": 2})),
    )
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)
    genesis = journal.recover().tail
    journal.append(
        _FIRST, StepState.RUNNING, expected_revision=0, at_ms=100,
        retained=genesis,
    )
    recovery = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", steps,
    ).recover(retained=genesis)
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    tip = ledger.reserve(
        derive_registered_atomic_intent(
            registry, steps[0].call, occurrence_id=_OCC_FIRST,
        ),
        retained=genesis_atomic_preaction_witness(),
    )
    return journal, recovery, ledger, tip, registry, steps, backend


def _review(fixture, *, tip=None):
    _journal, recovery, ledger, current, registry, steps, _backend = fixture
    return review_registered_planner_atomic_triage(
        recovery, steps, registry, ledger, current if tip is None else tip,
        _BINDINGS,
    )


def test_two_matching_local_write_intents_still_require_manual_review(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _journal, _recovery, ledger, tip, registry, steps, backend = fixture
    final_tip = ledger.reserve(
        derive_registered_atomic_intent(
            registry, steps[2].call, occurrence_id=_OCC_SECOND,
        ),
        retained=tip,
    )
    review = _review(fixture, tip=final_tip)
    assert review.retained_atomic_count == 2
    assert review.observations == (
        (_FIRST, "WRITE", "QUARANTINE_WRITE_UNKNOWN", "LOCAL_MATCH"),
        (_READ, "READ", "HOLD_UNCERTAIN", "NOT_APPLICABLE"),
        (_SECOND, "WRITE", "HELD_WRITE_APPROVAL", "LOCAL_MATCH"),
    )
    assert review.dispatch_authorized is False
    assert review.write_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.cross_store_atomicity_proven is False
    assert review.external_effect_proven is False
    assert review.manual_review_required is True
    assert backend.calls == 0


def test_atomic_commit_after_retained_witness_rejects_stale_join(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _journal, _recovery, ledger, retained, registry, steps, backend = fixture
    ledger.reserve(
        derive_registered_atomic_intent(
            registry, steps[2].call, occurrence_id=_OCC_SECOND,
        ),
        retained=retained,
    )
    with pytest.raises(RegisteredPlannerAtomicTriageRejected):
        _review(fixture)
    assert backend.calls == 0


def test_planner_commit_after_recovery_cannot_authorize_stale_join(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    journal, recovery, _ledger, _tip, _registry, _steps, backend = fixture
    # The separate Planner SQLite journal changes after the recovery image
    # was retained. The local join cannot claim a cross-store snapshot.
    journal.append(
        _FIRST, StepState.FAILED, expected_revision=1, at_ms=110,
        retained=recovery.tail,
    )
    review = _review(fixture)
    assert review.observations[0] == (
        _FIRST, "WRITE", "QUARANTINE_WRITE_UNKNOWN", "LOCAL_MATCH",
    )
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.cross_store_atomicity_proven is False
    assert review.external_effect_proven is False
    assert review.manual_review_required is True
    assert backend.calls == 0
