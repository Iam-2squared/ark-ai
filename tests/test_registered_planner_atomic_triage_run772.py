"""Joined Planner/registry/atomic recovery remains manual-only and disconnected.

The Planner and atomic SQLite files are separate transactions. In particular,
a locally matching prior WRITE does not resolve its unknown external outcome.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.disconnected_registered_planner_atomic_triage import (
    RegisteredPlannerAtomicTriage,
    RegisteredPlannerAtomicTriageRejected,
    review_registered_planner_atomic_triage,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry

_WRITE = "step_" + "1" * 16
_CHILD = "step_" + "2" * 16
_OTHER = "step_" + "3" * 16
_A = "occ_" + "a" * 64
_B = "occ_" + "b" * 64


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("manual recovery review cannot execute a tool")


def _setup(tmp_path: Path, *, running: bool = True, conflict: bool = False):
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
        ToolRegistration("reader", "fixture.read", Effect.READ, "local", backend),
    ))
    steps = (
        PlanStep(_WRITE, ToolCall("writer", "fixture.write", "local", {"value": 1})),
        PlanStep(
            _CHILD, ToolCall("reader", "fixture.read", "local", {"query": "one"}),
            (_WRITE,),
        ),
        PlanStep(_OTHER, ToolCall("writer", "fixture.write", "local", {"value": 2})),
    )
    plan_path = tmp_path / "plan.sqlite"
    journal = SyntheticPlanJournal(plan_path, steps)
    genesis = journal.recover().tail
    if running:
        journal.append(
            _WRITE, StepState.RUNNING, expected_revision=0, at_ms=100,
            retained=genesis,
        )
    recovered = SyntheticPlanJournal(plan_path, steps).recover(retained=genesis)
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    claim = derive_registered_atomic_intent(
        registry, steps[0].call, occurrence_id=_A,
    )
    if conflict:
        claim = AtomicIntentClaim(_A, "bound_" + "f" * 64, claim.request_sha256)
    tip = ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    return recovered, steps, registry, ledger, tip, backend


def _review(fixture, bindings=None):
    recovery, steps, registry, ledger, tip, _ = fixture
    if bindings is None:
        bindings = ((_WRITE, _A), (_OTHER, _B))
    return review_registered_planner_atomic_triage(
        recovery, steps, registry, ledger, tip, bindings,
    )


@pytest.mark.parametrize(
    ("running", "conflict", "expected_first"),
    ((True, False, "LOCAL_MATCH"), (True, True, "LOCAL_CONFLICT"),
     (False, False, "LOCAL_MATCH")),
)
def test_inert_join_preserves_unknown_write_and_independent_read_only_diagnosis(
    tmp_path: Path, running: bool, conflict: bool, expected_first: str,
) -> None:
    fixture = _setup(tmp_path, running=running, conflict=conflict)
    review = _review(fixture)
    assert type(review) is RegisteredPlannerAtomicTriage
    assert review.retained_atomic_count == 1
    assert len(review.observations) == 3
    assert review.observations[0] == (
        _WRITE, "WRITE",
        "QUARANTINE_WRITE_UNKNOWN" if running else "HELD_WRITE_APPROVAL",
        expected_first,
    )
    assert review.observations[1] == (
        _CHILD, "READ", "HOLD_UNCERTAIN" if running else "WAIT_DEPENDENCY",
        "NOT_APPLICABLE",
    )
    assert review.observations[2] == (
        _OTHER, "WRITE", "HELD_WRITE_APPROVAL", "ABSENT",
    )
    assert review.dispatch_authorized is False
    assert review.write_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.cross_store_atomicity_proven is False
    assert review.external_effect_proven is False
    assert review.manual_review_required is True
    assert fixture[-1].calls == 0


@pytest.mark.parametrize(
    "bindings",
    (
        ((_WRITE, _A),),
        ((_WRITE, _A), (_OTHER, _A)),
        ((_WRITE, _A), (_CHILD, _B)),
        ((_WRITE, _A), (_OTHER, "invalid")),
    ),
)
def test_missing_duplicate_read_bound_and_malformed_occurrences_fail_closed(
    tmp_path: Path, bindings,
) -> None:
    fixture = _setup(tmp_path)
    with pytest.raises(RegisteredPlannerAtomicTriageRejected):
        _review(fixture, bindings)
    assert fixture[-1].calls == 0


def test_recovery_status_forgery_is_not_accepted_from_detached_carrier(
    tmp_path: Path,
) -> None:
    recovered, steps, registry, ledger, tip, backend = _setup(tmp_path)
    forged = replace(
        recovered,
        step_statuses=tuple(
            (name, "failed" if name == _WRITE else state, revision)
            for name, state, revision in recovered.step_statuses
        ),
    )
    with pytest.raises(RegisteredPlannerAtomicTriageRejected):
        review_registered_planner_atomic_triage(
            forged, steps, registry, ledger, tip,
            ((_WRITE, _A), (_OTHER, _B)),
        )
    assert backend.calls == 0


def test_stale_atomic_tip_rejects_entire_plan_join(tmp_path: Path) -> None:
    recovered, steps, registry, ledger, _tip, backend = _setup(tmp_path)
    with pytest.raises(RegisteredPlannerAtomicTriageRejected):
        review_registered_planner_atomic_triage(
            recovered, steps, registry, ledger,
            genesis_atomic_preaction_witness(),
            ((_WRITE, _A), (_OTHER, _B)),
        )
    assert backend.calls == 0
