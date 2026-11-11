"""Quarantine witnesses must not trust replaceable dataclass equality.

All cases use disposable synthetic SQLite. No trusted clock, notification,
authenticated consent, automatic replay or external execution is involved.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark import disconnected_schedule_quarantine_ledger as quarantine


def _fixture(tmp_path):
    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine-equality.sqlite"
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    witness = quarantine.genesis_quarantine_witness(policy)
    return ledger, policy, path, witness


@pytest.mark.parametrize("operation", ("inspect", "write"))
def test_forged_equal_witness_never_bypasses_retained_cursor(
    tmp_path, monkeypatch, operation,
):
    ledger, policy, path, _genuine = _fixture(tmp_path)
    forged = quarantine.QuarantineWitness(0, "f" * 64)
    called = []

    def spoofed_equal(_self, _other):
        called.append(True)
        return True

    with monkeypatch.context() as patch:
        patch.setattr(quarantine.QuarantineWitness, "__eq__", spoofed_equal)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="stale or (changed|rolled-back) quarantine witness",
        ):
            if operation == "inspect":
                ledger.inspect(retained=forged)
            else:
                ledger.quarantine_expired(
                    index=0,
                    occurrence_id=quarantine.derive_quarantined_occurrence(policy, 0),
                    observed_ms=10_501,
                    retained=forged,
                )
    assert called == []
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (0,)


def test_valid_write_and_restarted_read_do_not_invoke_witness_equality(
    tmp_path, monkeypatch,
):
    ledger, policy, path, genesis = _fixture(tmp_path)
    touched = []

    def forbidden_equal(_self, _other):
        touched.append(True)
        raise AssertionError("untrusted QuarantineWitness equality executed")

    with monkeypatch.context() as patch:
        patch.setattr(quarantine.QuarantineWitness, "__eq__", forbidden_equal)
        receipt = ledger.quarantine_expired(
            index=0,
            occurrence_id=quarantine.derive_quarantined_occurrence(policy, 0),
            observed_ms=10_501,
            retained=genesis,
        )
        restarted = quarantine.DisconnectedScheduleQuarantineLedger(
            path, policy=policy,
        )
        inspected = restarted.inspect(retained=receipt.witness)
    assert touched == []
    assert inspected.count == receipt.witness.count == 1
    assert inspected.chain_sha256 == receipt.witness.chain_sha256
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)
