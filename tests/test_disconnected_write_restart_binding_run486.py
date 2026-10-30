"""Synthetic Planner WRITE recovery binds reservations but never replays."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_write_restart_binding as binding
from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
)
from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)


def _identities(n=1, plan_number=1):
    plan = "plan_" + f"{plan_number:064x}"
    step = "step_" + f"{n:016x}"
    request = f"{n:064x}"
    slot = derive_disconnected_write_slot_id(plan, step, request)
    return plan, step, request, slot


def _setup(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "write_slots.sqlite", create=True)
    return ledger, genesis_write_slot_witness()


def _reserve(ledger, retained, *, n=1, plan_number=1):
    plan, step, request, slot = _identities(n, plan_number)
    claim = DetachedWriteSlotClaim(slot, plan, step, request)
    next_witness = ledger.reserve_many((claim,), retained=retained).witness
    return next_witness, (plan, step, slot)


def _review(ledger, retained, plan, steps):
    return binding.review_disconnected_write_restart(ledger, retained, plan, steps)


def test_unknown_reserved_write_remains_quarantined_after_restart(tmp_path):
    ledger, retained = _setup(tmp_path)
    current, (plan, step, slot) = _reserve(ledger, retained)
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN", None, slot)
    restarted = DisconnectedWriteSlotLedger(tmp_path / "write_slots.sqlite")
    result = _review(restarted, current, plan, (claim,))
    assert result.total_steps == 1
    assert result.reserved_write_steps == 1
    assert result.quarantined_write_steps == 1
    assert len(result.fingerprint) == 64
    assert result.tool_dispatch_authorized is False
    assert result.write_replay_authorized is False
    assert result.external_outcome_verified is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert result.cross_store_atomicity_proven is False
    assert restarted.inspect(retained=current) == current


@pytest.mark.parametrize("state", ["UNKNOWN", "RUNNING", "PENDING"])
def test_reserved_write_state_never_releases_dispatch(tmp_path, state):
    ledger, retained = _setup(tmp_path)
    current, (plan, step, slot) = _reserve(ledger, retained)
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), state, None, slot)
    result = _review(ledger, current, plan, (claim,))
    assert result.reserved_write_steps == 1
    assert result.tool_dispatch_authorized is False
    assert result.write_replay_authorized is False


def test_unreserved_unknown_write_is_quarantined_not_replayed(tmp_path):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    result = _review(ledger, retained, plan, (claim,))
    assert result.reserved_write_steps == 0
    assert result.quarantined_write_steps == 1
    assert result.write_replay_authorized is False


def test_detached_read_ready_is_not_a_real_execution_grant(tmp_path):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "READ", (), "PENDING")
    result = _review(ledger, retained, plan, (claim,))
    assert result.reserved_write_steps == 0
    assert result.quarantined_write_steps == 0
    assert result.tool_dispatch_authorized is False


def test_mismatched_slot_is_not_accepted_as_membership(tmp_path):
    ledger, retained = _setup(tmp_path)
    current, (plan, step, _) = _reserve(ledger, retained)
    wrong_slot = _identities(2)[3]
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN", None, wrong_slot)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="not bound"):
        _review(ledger, current, plan, (claim,))


def test_slot_from_another_plan_is_not_accepted(tmp_path):
    ledger, retained = _setup(tmp_path)
    current, (_, step, slot) = _reserve(ledger, retained, plan_number=2)
    other_plan = _identities(1, plan_number=1)[0]
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN", None, slot)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="not bound"):
        _review(ledger, current, other_plan, (claim,))


def test_stale_retained_witness_cannot_reconcile_after_commit(tmp_path):
    ledger, retained = _setup(tmp_path)
    _, (plan, step, slot) = _reserve(ledger, retained)
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN", None, slot)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="history differs"):
        _review(ledger, retained, plan, (claim,))


def test_invalid_claim_not_persisted_or_retried(tmp_path):
    ledger, retained = _setup(tmp_path)
    plan, step, _, slot = _identities()
    bad = OfflineRecoveryStepClaim(step, "WRITE", (), "UNSUPPORTED", None, slot)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="quarantine denied"):
        _review(ledger, retained, plan, (bad,))
    assert ledger.inspect(retained=retained) == retained


def test_callback_mutation_of_retained_witness_is_rejected(tmp_path, monkeypatch):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    original = binding.review_disconnected_recovery_fence

    def mutate(*args):
        result = original(*args)
        object.__setattr__(retained, "chain_sha256", "f" * 64)
        return result

    monkeypatch.setattr(binding, "review_disconnected_recovery_fence", mutate)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="carriers changed"):
        _review(ledger, retained, plan, (claim,))


def test_forged_quarantine_result_is_rejected(tmp_path, monkeypatch):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    monkeypatch.setattr(binding, "review_disconnected_recovery_fence", lambda *a: object())
    with pytest.raises(binding.OfflineWriteRestartRejected, match="result invalid"):
        _review(ledger, retained, plan, (claim,))


def test_post_read_synthetic_history_mutation_is_detected(tmp_path, monkeypatch):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    original = ledger.inspect

    def change(*, retained):
        current = original(retained=retained)
        fresh = DetachedWriteSlotClaim(
            _identities(2)[3], _identities(2)[0], _identities(2)[1], _identities(2)[2],
        )
        ledger.reserve_many((fresh,), retained=current)
        return current

    monkeypatch.setattr(ledger, "inspect", change)
    with pytest.raises(binding.OfflineWriteRestartRejected, match="changed after read"):
        _review(ledger, retained, plan, (claim,))


def test_result_constructor_cannot_claim_write_authority(tmp_path, monkeypatch):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    monkeypatch.setattr(binding, "OfflineWriteRestartReport", lambda *a: object())
    with pytest.raises(binding.OfflineWriteRestartRejected, match="acquired authority"):
        _review(ledger, retained, plan, (claim,))


def test_exact_type_witness_guard(tmp_path):
    ledger, retained = _setup(tmp_path)
    plan, step, _, _ = _identities()
    claim = OfflineRecoveryStepClaim(step, "WRITE", (), "UNKNOWN")
    bad = replace(retained, count=True)
    with pytest.raises(ValueError):
        _review(ledger, bad, plan, (claim,))
