"""Synthetic overdue-quarantine receipts are never execution authority.

All mutations affect only a temporary fixture SQLite file; no notifications,
Tools, real scheduler dispatch, or external effects are performed.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark import disconnected_schedule_quarantine_ledger as mod


def _fixture(tmp_path):
    policy = mod.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "expired-quarantine.sqlite"
    ledger = mod.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, mod.genesis_quarantine_witness(policy)


def _write(ledger, policy, retained):
    return ledger.quarantine_expired(
        index=0,
        occurrence_id=mod.derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=retained,
    )


@pytest.mark.parametrize("authority", (
    "execution_authorized", "notification_authorized",
    "automatic_replay_authorized", "trusted_clock_verified", "consent_verified",
))
def test_postcommit_authority_forgery_never_enables_overdue_execution(
    tmp_path, monkeypatch, authority,
):
    ledger, policy, retained = _fixture(tmp_path)
    monkeypatch.setattr(
        mod.QuarantineReceipt, authority, property(lambda self: True),
    )
    with pytest.raises(mod.ScheduleQuarantineRejected, match="gained authority"):
        _write(ledger, policy, retained)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


@pytest.mark.parametrize("mutation", ("witness", "policy"))
def test_false_final_getter_cannot_mutate_returned_quarantine_epoch(
    tmp_path, monkeypatch, mutation,
):
    ledger, policy, retained = _fixture(tmp_path)

    def malicious(self):
        if mutation == "witness":
            object.__setattr__(self.witness, "chain_sha256", "f" * 64)
        else:
            ledger._epoch = tuple(list(ledger._epoch))
        return False

    monkeypatch.setattr(
        mod.QuarantineReceipt, "consent_verified", property(malicious),
    )
    with pytest.raises(mod.ScheduleQuarantineRejected, match="post-commit|carrier"):
        _write(ledger, policy, retained)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


def test_false_final_getter_cannot_silently_change_durable_history(
    tmp_path, monkeypatch,
):
    ledger, policy, retained = _fixture(tmp_path)

    def malicious(_self):
        with sqlite3.connect(ledger._path) as conn:
            conn.execute("UPDATE quarantines SET observed_ms=observed_ms+1 WHERE seq=1")
        return False

    monkeypatch.setattr(
        mod.QuarantineReceipt, "consent_verified", property(malicious),
    )
    with pytest.raises(mod.ScheduleQuarantineRejected, match="chain altered|history"):
        _write(ledger, policy, retained)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


def test_false_final_getter_cannot_rebind_denial_descriptor(
    tmp_path, monkeypatch,
):
    ledger, policy, retained = _fixture(tmp_path)

    def malicious(_self):
        monkeypatch.setattr(
            mod.QuarantineReceipt, "consent_verified", property(lambda self: False),
        )
        return False

    monkeypatch.setattr(
        mod.QuarantineReceipt, "consent_verified", property(malicious),
    )
    with pytest.raises(mod.ScheduleQuarantineRejected, match="result epoch"):
        _write(ledger, policy, retained)


def test_normal_quarantine_restarts_as_only_history_not_dispatch(tmp_path):
    ledger, policy, retained = _fixture(tmp_path)
    receipt = _write(ledger, policy, retained)
    assert receipt.quarantined_index == 0
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
    assert mod.DisconnectedScheduleQuarantineLedger(
        ledger._path, policy=policy,
    ).inspect(retained=receipt.witness) == receipt.witness
    with pytest.raises(mod.ScheduleQuarantineRejected, match="stale"):
        _write(ledger, policy, retained)
