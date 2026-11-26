"""A two-read Planner freshness check cannot grant cross-store execution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import ark.agency.disconnected_epoch_bound_atomic_triage as integration
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.disconnected_epoch_bound_atomic_triage import (
    EpochBoundAtomicTriage,
    EpochBoundAtomicTriageRejected,
    review_epoch_bound_atomic_triage,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry

_WRITE = "step_" + "1" * 16
_READ = "step_" + "2" * 16
_OCC = "occ_" + "a" * 64


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("diagnosis must not call backend")


def _setup(tmp_path: Path):
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
        ToolRegistration("reader", "fixture.read", Effect.READ, "local", backend),
    ))
    steps = (
        PlanStep(_WRITE, ToolCall("writer", "fixture.write", "local", {"v": 1})),
        PlanStep(
            _READ, ToolCall("reader", "fixture.read", "local", {"q": 1}),
            (_WRITE,),
        ),
    )
    journal = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps)
    genesis = journal.recover().tail
    running = journal.append(
        _WRITE, StepState.RUNNING, expected_revision=0, at_ms=100,
        retained=genesis,
    )
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    claim = derive_registered_atomic_intent(
        registry, steps[0].call, occurrence_id=_OCC,
    )
    tip = ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    args = (journal, running, genesis, steps, registry, ledger, tip, ((_WRITE, _OCC),))
    return args, backend


def test_matching_two_reads_preserve_manual_only_quarantine(
    tmp_path: Path,
) -> None:
    args, backend = _setup(tmp_path)
    result = review_epoch_bound_atomic_triage(*args)
    assert type(result) is EpochBoundAtomicTriage
    assert result.plan_id == args[1].tail.topology_digest
    assert result.planner_event_count == 1
    assert result.retained_atomic_count == 1
    assert result.observations == (
        (_WRITE, "WRITE", "QUARANTINE_WRITE_UNKNOWN", "LOCAL_MATCH"),
        (_READ, "READ", "HOLD_UNCERTAIN", "NOT_APPLICABLE"),
    )
    assert result.dispatch_authorized is False
    assert result.write_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.cross_store_atomicity_proven is False
    assert result.freshness_after_return_proven is False
    assert result.external_effect_proven is False
    assert result.manual_review_required is True
    assert backend.calls == 0


def test_later_planner_commit_invalidates_old_match(
    tmp_path: Path,
) -> None:
    args, backend = _setup(tmp_path)
    earlier = review_epoch_bound_atomic_triage(*args)
    args[0].append(
        _WRITE, StepState.FAILED, expected_revision=1, at_ms=110,
        retained=args[1].tail,
    )
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*args)
    assert earlier.freshness_after_return_proven is False
    assert backend.calls == 0


def test_retained_planner_prefix_forgery_rejected(tmp_path: Path) -> None:
    args, backend = _setup(tmp_path)
    bad = list(args)
    bad[2] = replace(args[2], event_hash="pevt_" + "f" * 64)
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*bad)
    assert backend.calls == 0


def test_stale_atomic_witness_rejected(tmp_path: Path) -> None:
    args, backend = _setup(tmp_path)
    bad = list(args)
    bad[6] = genesis_atomic_preaction_witness()
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*bad)
    assert backend.calls == 0


def test_wrong_exact_journal_type_rejected(tmp_path: Path) -> None:
    args, backend = _setup(tmp_path)
    bad = list(args)
    bad[0] = object()
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*bad)
    assert backend.calls == 0


def test_replaced_recheck_callback_rejected_before_any_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, backend = _setup(tmp_path)
    called: list[str] = []

    def forged(*_args):
        called.append("unsafe")
        return None

    monkeypatch.setattr(
        integration, "recheck_disconnected_planner_epoch", forged,
    )
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*args)
    assert called == []
    assert backend.calls == 0


def test_result_denial_descriptor_replacement_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, backend = _setup(tmp_path)
    monkeypatch.setattr(
        EpochBoundAtomicTriage, "dispatch_authorized", property(lambda _self: True),
    )
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*args)
    assert backend.calls == 0
