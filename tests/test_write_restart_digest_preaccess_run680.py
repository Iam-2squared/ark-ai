"""Offline WRITE restart digest primitives must be original and non-reentrant.

This tests only local SQLite fixtures and synthetic quarantine claims. A
matching ledger has no real execution/consent/replay or trusted time authority.
"""

import pytest

import ark.agency.disconnected_write_restart_binding as binding
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "b" * 16


def _case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "write-restart.sqlite", create=True)
    retained = genesis_write_slot_witness()
    step = OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN")
    return ledger, retained, (step,)


def _poison(monkeypatch, target):
    if target == "sha256":
        monkeypatch.setattr(
            binding.hashlib, "sha256",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("untrusted sha256 invoked"),
            ),
        )
    elif target == "json":
        monkeypatch.setattr(
            binding.json, "dumps",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("untrusted serializer invoked"),
            ),
        )
    else:
        monkeypatch.setattr(binding, "_DOMAIN", binding._DOMAIN + b"changed")


@pytest.mark.parametrize("target", ("sha256", "json", "domain"))
def test_bad_digest_primitives_denied_before_private_sqlite(
    tmp_path, monkeypatch, target,
):
    ledger, retained, steps = _case(tmp_path)
    touched = []

    def prohibited_open(*_args, **_kwargs):
        touched.append(True)
        raise AssertionError("private SQLite access must not occur")

    monkeypatch.setattr(ledger, "_open", prohibited_open)
    _poison(monkeypatch, target)
    with pytest.raises(
        binding.OfflineWriteRestartRejected,
        match="digest implementation changed",
    ):
        binding.review_disconnected_write_restart(ledger, retained, PLAN, steps)
    assert not touched


@pytest.mark.parametrize("target", ("json", "domain"))
def test_digest_primitive_drift_after_planner_callback_is_rejected(
    tmp_path, monkeypatch, target,
):
    ledger, retained, steps = _case(tmp_path)
    original = binding.review_disconnected_recovery_fence
    callbacks = []

    def drift(*args):
        result = original(*args)
        callbacks.append(True)
        _poison(monkeypatch, target)
        return result

    monkeypatch.setattr(binding, "review_disconnected_recovery_fence", drift)
    with pytest.raises(
        binding.OfflineWriteRestartRejected,
        match="digest implementation changed",
    ):
        binding.review_disconnected_write_restart(ledger, retained, PLAN, steps)
    assert callbacks == [True]


def test_original_hashing_quarantines_unknown_write_without_retry(tmp_path):
    ledger, retained, steps = _case(tmp_path)
    result = binding.review_disconnected_write_restart(ledger, retained, PLAN, steps)
    assert len(result.fingerprint) == 64
    assert result.quarantined_write_steps == 1
    assert result.tool_dispatch_authorized is False
    assert result.write_replay_authorized is False
    assert result.consent_verified is False
    assert result.cross_store_atomicity_proven is False
