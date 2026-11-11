"""Detached Planner recovery must not change during final atomic inspection.

Inert synthetic SQLite only. Neither a matching local witness nor rejection
grants dispatch, human consent, or external exactly-once authority.
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

_STEP = "step_" + "1" * 16
_OCCURRENCE = "occ_" + "a" * 64


class InertBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("manual-only Planner diagnostic dispatched a tool")


def _case(tmp_path: Path):
    backend = InertBackend()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
    ))
    steps = (
        PlanStep(
            _STEP, ToolCall("writer", "fixture.write", "local", {"synthetic": 1}),
        ),
    )
    journal = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps)
    genesis = journal.recover().tail
    recovered = journal.append(
        _STEP, StepState.RUNNING, expected_revision=0, at_ms=100,
        retained=genesis,
    )
    ledger = DisconnectedAtomicPreactionLedger.create(
        tmp_path / "atomic.sqlite",
    )
    intent = derive_registered_atomic_intent(
        registry, steps[0].call, occurrence_id=_OCCURRENCE,
    )
    atomic_tail = ledger.reserve(
        intent, retained=genesis_atomic_preaction_witness(),
    )
    args = (
        journal, recovered, genesis, steps, registry, ledger, atomic_tail,
        ((_STEP, _OCCURRENCE),),
    )
    return args, backend


@pytest.mark.parametrize(
    "mutation",
    ("recovered_tail_value", "retained_tail_value", "recovery_status_carrier"),
)
def test_final_atomic_callback_cannot_retarget_prior_planner_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
):
    args, backend = _case(tmp_path)
    recovered, retained, ledger = args[1], args[2], args[5]
    old_open = ledger._open
    changed = []

    def change_during_last_atomic_read(*, read_only: bool):
        # The registered atomic reviewer invokes its own pinned reader.
        # This instance _open hook is reached at the final standalone
        # atomic inspection, after both Planner reads have matched.
        monkeypatch.setattr(ledger, "_open", old_open)
        changed.append(mutation)
        if mutation == "recovered_tail_value":
            object.__setattr__(
                recovered.tail, "event_count", recovered.tail.event_count + 1,
            )
        elif mutation == "retained_tail_value":
            object.__setattr__(
                retained, "event_hash", "pevt_" + "f" * 64,
            )
        else:
            replacement = tuple(list(recovered.step_statuses))
            assert replacement == recovered.step_statuses
            assert replacement is not recovered.step_statuses
            object.__setattr__(recovered, "step_statuses", replacement)
        return old_open(read_only=read_only)

    monkeypatch.setattr(ledger, "_open", change_during_last_atomic_read)
    # A changed recovered count can be rejected by the earlier Planner
    # cross-store comparison; both outcomes must fail closed without dispatch.
    message = (
        "Planner changed across atomic review"
        if mutation == "recovered_tail_value"
        else "Planner recovery input epoch changed"
    )
    with pytest.raises(EpochBoundAtomicTriageRejected, match=message):
        review_epoch_bound_atomic_triage(*args)
    assert changed == [mutation]
    assert backend.calls == 0


def test_unchanged_planner_image_still_returns_no_authority(tmp_path: Path):
    args, backend = _case(tmp_path)
    result = review_epoch_bound_atomic_triage(*args)
    assert result.planner_event_count == 1
    assert result.retained_atomic_count == 1
    assert result.dispatch_authorized is False
    assert result.write_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.cross_store_atomicity_proven is False
    assert result.freshness_after_return_proven is False
    assert result.external_effect_proven is False
    assert result.manual_review_required is True
    assert backend.calls == 0
