"""Synthetic Planner WRITE restart must reject patched witness equality.

Disconnected SQLite fixtures only. No ToolBackend, replay, or user permission.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_write_restart_binding as restart
from ark.agency import disconnected_write_slot_ledger as slots
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim


def _setup(tmp_path):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "writes.sqlite", create=True)
    old = slots.genesis_write_slot_witness()
    plan = "plan_" + "a" * 64
    step = "step_" + "b" * 16
    request = "c" * 64
    slot = slots.derive_disconnected_write_slot_id(plan, step, request)
    claim = slots.DetachedWriteSlotClaim(slot, plan, step, request)
    current = ledger.reserve_many((claim,), retained=old).witness
    review = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN", None, slot)
    return ledger, old, current, plan, (review,)


def test_stale_restart_is_rejected_with_always_true_witness_equality(
    tmp_path, monkeypatch,
):
    ledger, old, _, plan, steps = _setup(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        with pytest.raises(
            restart.OfflineWriteRestartRejected, match="durable WRITE history differs",
        ):
            restart.review_disconnected_write_restart(ledger, old, plan, steps)


@pytest.mark.parametrize(("stage", "error"), [
    (1, "durable WRITE history differs"),
    (2, "WRITE ledger changed during review"),
    (3, "WRITE ledger changed after read"),
    (4, "WRITE ledger changed after final authority denial"),
])
def test_each_independent_read_rejects_forged_scalar_tip_with_true_equality(
    tmp_path, monkeypatch, stage, error,
):
    ledger, _, retained, plan, steps = _setup(tmp_path)
    original = restart._inspect
    calls = 0

    def forged_read(conn):
        nonlocal calls
        calls += 1
        value = original(conn)
        if calls == stage:
            different = "f" * 64 if value.chain_sha256 != "f" * 64 else "0" * 64
            return slots.WriteSlotLedgerWitness(value.count, different)
        return value

    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        patch.setattr(restart, "_inspect", forged_read)
        with pytest.raises(restart.OfflineWriteRestartRejected, match=error):
            restart.review_disconnected_write_restart(ledger, retained, plan, steps)
    assert calls == stage
    assert ledger.inspect(retained=retained).count == 1


def test_public_reinspection_callback_cannot_claim_forged_tip(
    tmp_path, monkeypatch,
):
    ledger, _, retained, plan, steps = _setup(tmp_path)

    def forged_inspect(*, retained):
        alternate = "f" * 64 if retained.chain_sha256 != "f" * 64 else "0" * 64
        return slots.WriteSlotLedgerWitness(retained.count, alternate)

    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        patch.setattr(ledger, "inspect", forged_inspect)
        with pytest.raises(
            restart.OfflineWriteRestartRejected, match="WRITE ledger changed after read",
        ):
            restart.review_disconnected_write_restart(ledger, retained, plan, steps)


def test_valid_quarantined_restart_succeeds_with_always_false_equality(
    tmp_path, monkeypatch,
):
    ledger, _, retained, plan, steps = _setup(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: False)
        report = restart.review_disconnected_write_restart(ledger, retained, plan, steps)
    assert report.reserved_write_steps == 1
    assert report.quarantined_write_steps == 1
    assert report.tool_dispatch_authorized is False
    assert report.write_replay_authorized is False
    assert report.cross_store_atomicity_proven is False
