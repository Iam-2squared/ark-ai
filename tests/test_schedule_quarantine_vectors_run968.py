"""Run968: proactive quarantine denies vector and authority drift before SQLite write.

Disposable synthetic SQLite only; a quarantine receipt never authorizes
execution, notification, replay, consent, or trusted-clock claims.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_schedule_quarantine_ledger as quarantine


def _fixture(tmp_path):
    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "proactive-vector-run968.sqlite"
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    witness = quarantine.genesis_quarantine_witness(policy)
    occurrence = quarantine.derive_quarantined_occurrence(policy, 0)
    return path, ledger, witness, occurrence


def _write(ledger, witness, occurrence):
    return ledger.quarantine_expired(
        index=0, occurrence_id=occurrence, observed_ms=10_501,
        retained=witness,
    )


def _assert_no_quarantines(path):
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM quarantines"
        ).fetchone() == (0,)


@pytest.mark.parametrize("vector", (
    "_RECEIPT_CARRIER_NAMES", "_ORIGINAL_RECEIPT_CARRIER",
))
@pytest.mark.parametrize("slot", ("witness", "quarantined_index"))
def test_receipt_vector_truncation_denied_before_write(
    tmp_path, monkeypatch, vector, slot,
):
    path, ledger, witness, occurrence = _fixture(tmp_path)
    called = []

    def poison(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("replaced receipt getter must not execute")

    with monkeypatch.context() as patch:
        patch.setattr(quarantine, vector, ())
        patch.setattr(quarantine.QuarantineReceipt, slot, property(poison))
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="receipt constructor or field descriptor changed",
        ):
            _write(ledger, witness, occurrence)

    assert called == []
    _assert_no_quarantines(path)


@pytest.mark.parametrize("vector", (
    "_POLICY_INPUT_FIELDS", "_WITNESS_INPUT_FIELDS", "_INPUT_HOOKS",
    "_POLICY_INPUT_ORIGINALS", "_WITNESS_INPUT_ORIGINALS",
))
@pytest.mark.parametrize("operation", ("inspect", "write"))
def test_input_vector_replacement_denied_before_retained_field_access(
    tmp_path, monkeypatch, vector, operation,
):
    path, ledger, witness, occurrence = _fixture(tmp_path)
    called = []

    def poison(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("replaced input getter must not execute")

    target = (
        quarantine.QuarantinePolicy
        if vector.startswith("_POLICY") else quarantine.QuarantineWitness
    )
    slot = "first_ms" if target is quarantine.QuarantinePolicy else "count"
    with monkeypatch.context() as patch:
        patch.setattr(quarantine, vector, ())
        patch.setattr(target, slot, property(poison))
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="quarantine input carrier descriptor changed",
        ):
            if operation == "inspect":
                ledger.inspect(retained=witness)
            else:
                _write(ledger, witness, occurrence)

    assert called == []
    _assert_no_quarantines(path)


@pytest.mark.parametrize("target,property_name", (
    ("receipt", "execution_authorized"),
    ("receipt", "notification_authorized"),
    ("witness", "independently_authenticated"),
))
def test_original_denial_descriptor_checked_before_quarantine_commit(
    tmp_path, monkeypatch, target, property_name,
):
    path, ledger, witness, occurrence = _fixture(tmp_path)
    called = []

    def poison(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("replacement authority property must not execute")

    cls = (
        quarantine.QuarantineReceipt if target == "receipt"
        else quarantine.QuarantineWitness
    )
    with monkeypatch.context() as patch:
        patch.setattr(cls, property_name, property(poison))
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="receipt constructor or field descriptor changed",
        ):
            _write(ledger, witness, occurrence)

    assert called == []
    _assert_no_quarantines(path)


def test_original_quarantine_flow_stays_non_authorizing(tmp_path):
    path, ledger, witness, occurrence = _fixture(tmp_path)
    receipt = _write(ledger, witness, occurrence)
    assert receipt.quarantined_index == 0
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
    assert receipt.witness.independently_authenticated is False
    restarted = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=quarantine.QuarantinePolicy(
            "a" * 64, 10_000, 5_000, 3, 500,
        ), create=False,
    )
    assert restarted.inspect(retained=receipt.witness) == receipt.witness
