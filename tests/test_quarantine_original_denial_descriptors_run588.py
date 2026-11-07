"""Original deny-only quarantine descriptors remain immutable in fixture results.

This test never dispatches, notifies, executes tools, or authenticates a caller.
A failed post-commit receipt review must not roll back or auto-retry the
already persisted synthetic quarantine event.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineReceipt,
    QuarantineWitness,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_FLAGS = (
    "execution_authorized",
    "notification_authorized",
    "automatic_replay_authorized",
    "trusted_clock_verified",
    "consent_verified",
)


def _setup(tmp_path):
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, genesis_quarantine_witness(policy), path


def _append(ledger, policy, prior):
    return ledger.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=prior,
    )


@pytest.mark.parametrize("flag", _FLAGS)
def test_preinstalled_false_receipt_descriptor_not_accepted(
    tmp_path, monkeypatch, flag,
):
    ledger, policy, prior, path = _setup(tmp_path)
    monkeypatch.setattr(QuarantineReceipt, flag, property(lambda _: False))
    with pytest.raises(ScheduleQuarantineRejected, match="original denial"):
        _append(ledger, policy, prior)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)
    with pytest.raises(ScheduleQuarantineRejected, match="stale"):
        ledger.inspect(retained=prior)


def test_preinstalled_false_witness_authentication_descriptor_not_accepted(
    tmp_path, monkeypatch,
):
    ledger, policy, prior, path = _setup(tmp_path)
    monkeypatch.setattr(
        QuarantineWitness, "independently_authenticated",
        property(lambda _: False),
    )
    with pytest.raises(ScheduleQuarantineRejected, match="original denial"):
        _append(ledger, policy, prior)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


def test_original_quarantine_receipt_remains_deny_only_after_restart(tmp_path):
    ledger, policy, prior, path = _setup(tmp_path)
    receipt = _append(ledger, policy, prior)
    assert receipt.quarantined_index == 0
    assert receipt.witness.independently_authenticated is False
    assert all(getattr(receipt, flag) is False for flag in _FLAGS)
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert reopened.inspect(retained=receipt.witness) == receipt.witness
