"""An atomic reservation during Planner recheck cannot redeem a stale tip.

All execution backends are inert. No external approval or real action exists.
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
from ark.agency.disconnected_epoch_bound_atomic_triage import (
    EpochBoundAtomicTriageRejected,
    review_epoch_bound_atomic_triage,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry

_WRITE = "step_" + "1" * 16
_OCC = "occ_" + "a" * 64
_SECOND = "occ_" + "b" * 64


class NoBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("diagnostic invoked a backend")


def _fixture(tmp_path: Path):
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
    ))
    steps = (
        PlanStep(_WRITE, ToolCall("writer", "fixture.write", "local", {"v": 1})),
    )
    journal = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps)
    genesis = journal.recover().tail
    recovered = journal.append(
        _WRITE, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    first = derive_registered_atomic_intent(
        registry, steps[0].call, occurrence_id=_OCC,
    )
    tip = ledger.reserve(first, retained=genesis_atomic_preaction_witness())
    args = (journal, recovered, genesis, steps, registry, ledger, tip, ((_WRITE, _OCC),))
    return args, backend


def test_atomic_commit_between_triage_and_final_tail_read_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, backend = _fixture(tmp_path)
    ledger, retained, registry, steps = args[5], args[6], args[4], args[3]
    original_open = ledger._open
    committed = []

    def inject_before_last_snapshot(*, read_only: bool):
        # The earlier registry batch uses its pinned class reader, whereas
        # inspect() uses this ordinary instance opening path. Model a new
        # independent writer committing at that exact interleaving.
        monkeypatch.setattr(ledger, "_open", original_open)
        second = derive_registered_atomic_intent(
            registry, steps[0].call, occurrence_id=_SECOND,
        )
        committed.append(ledger.reserve(second, retained=retained))
        return original_open(read_only=read_only)

    monkeypatch.setattr(ledger, "_open", inject_before_last_snapshot)
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*args)
    assert len(committed) == 1
    assert committed[0].count == 2
    assert backend.calls == 0


def test_replaced_atomic_tail_reader_rejected_before_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, backend = _fixture(tmp_path)
    called = []

    def unsafe_reader(_self, _retained):
        called.append(True)
        raise AssertionError("must not call substituted ledger reader")

    monkeypatch.setattr(
        DisconnectedAtomicPreactionLedger, "inspect", unsafe_reader,
    )
    with pytest.raises(EpochBoundAtomicTriageRejected):
        review_epoch_bound_atomic_triage(*args)
    assert called == []
    assert backend.calls == 0


def test_matching_planner_and_atomic_tail_remain_manual_only(
    tmp_path: Path,
) -> None:
    args, backend = _fixture(tmp_path)
    result = review_epoch_bound_atomic_triage(*args)
    assert result.retained_atomic_count == 1
    assert result.planner_event_count == 1
    assert result.observations == (
        (_WRITE, "WRITE", "QUARANTINE_WRITE_UNKNOWN", "LOCAL_MATCH"),
    )
    assert result.dispatch_authorized is False
    assert result.write_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.cross_store_atomicity_proven is False
    assert result.freshness_after_return_proven is False
    assert result.external_effect_proven is False
    assert result.manual_review_required is True
    assert backend.calls == 0
