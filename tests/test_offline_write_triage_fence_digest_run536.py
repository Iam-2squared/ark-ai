"""Parent-owned canonical fence verification for manual-only WRITE triage."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import offline_write_manual_triage as triage
from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryDisposition,
    OfflineRecoveryStepClaim,
)
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
FIRST = "step_" + "1" * 16
SECOND = "step_" + "2" * 16


def _inputs(tmp_path):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "write-slots.sqlite").resolve(), create=True,
    )
    steps = (
        OfflineRecoveryStepClaim(FIRST, "READ", (), "SUCCEEDED", "c" * 64),
        OfflineRecoveryStepClaim(SECOND, "WRITE", (FIRST,), "UNKNOWN"),
    )
    return ledger, genesis_write_slot_witness(), steps


def test_valid_fence_reconciles_without_action(tmp_path):
    ledger, retained, steps = _inputs(tmp_path)
    result = triage.build_offline_write_triage_packet(
        ledger, retained, PLAN, steps,
    )
    assert len(result.items) == 1
    assert result.items[0].step_id == SECOND
    assert result.items[0].investigation == "UNKNOWN_EFFECT_HOLD"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.human_review_completed is False


@pytest.mark.parametrize("kind", (
    "wrong_type", "wrong_digest", "wrong_plan", "wrong_code",
    "wrong_step", "short_decisions", "wrong_decision_type",
))
def test_parent_rejects_forged_child_fence(tmp_path, monkeypatch, kind):
    ledger, retained, steps = _inputs(tmp_path)
    actual = triage.review_disconnected_recovery_fence

    def forged(plan_id, claims):
        original = actual(plan_id, claims)
        if kind == "wrong_type":
            return object()
        if kind == "wrong_digest":
            return replace(original, digest="0" * 64)
        if kind == "wrong_plan":
            return replace(original, plan_id="plan_" + "f" * 64)
        if kind == "short_decisions":
            return replace(original, decisions=original.decisions[:1])
        if kind == "wrong_decision_type":
            return replace(original, decisions=(object(), *original.decisions[1:]))
        first = original.decisions[0]
        if kind == "wrong_code":
            mutated = replace(first, code="WRITE_AUTHORIZED")
        else:
            mutated = replace(first, step_id=SECOND)
        return replace(original, decisions=(mutated, *original.decisions[1:]))

    monkeypatch.setattr(triage, "review_disconnected_recovery_fence", forged)
    with pytest.raises(triage.OfflineWriteTriageRejected):
        triage.build_offline_write_triage_packet(
            ledger, retained, PLAN, steps,
        )


def test_false_authority_property_cannot_mutate_fence_digest(tmp_path, monkeypatch):
    ledger, retained, steps = _inputs(tmp_path)
    from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryFence

    def mutate(self):
        object.__setattr__(self, "digest", "f" * 64)
        return False

    monkeypatch.setattr(OfflineRecoveryFence, "write_authorized", property(mutate))
    with pytest.raises((triage.OfflineWriteTriageRejected, ValueError)):
        triage.build_offline_write_triage_packet(
            ledger, retained, PLAN, steps,
        )


def test_false_authority_property_cannot_rewrite_disposition(tmp_path, monkeypatch):
    ledger, retained, steps = _inputs(tmp_path)

    def mutate(self):
        object.__setattr__(self, "code", "READY_MOCK_ONLY")
        return False

    # An ordinary exact disposition cannot mint permission even if reflective
    # callbacks later mutate it. The parent requires the canonical fence.
    monkeypatch.setattr(
        OfflineRecoveryDisposition, "write_authorized", property(mutate),
        raising=False,
    )
    result = triage.build_offline_write_triage_packet(
        ledger, retained, PLAN, steps,
    )
    assert result.automatic_replay_authorized is False
    assert result.items[0].disposition == "QUARANTINE_WRITE_UNKNOWN"
