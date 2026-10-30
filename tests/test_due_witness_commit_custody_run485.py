"""Scheduler: retained due witness cannot acquire authority or drift post-commit."""

from __future__ import annotations

import sqlite3

import pytest

import ark.agency.disconnected_due_reservation as due


def _new(tmp_path):
    ledger = due.DisconnectedDueReservations(tmp_path / "due.sqlite3")
    return ledger, ledger.witness()


def _reserve(store, witness):
    return store.reserve_due(
        policy_sha256="a" * 64, due_at_ms=100, observed_now_ms=101,
        retained=witness,
    )


def test_forged_retained_witness_authority_rejected_before_reservation(
    tmp_path, monkeypatch,
):
    store, original = _new(tmp_path)
    monkeypatch.setattr(
        due.DueReservationWitness, "independent_custody_proven",
        property(lambda self: True),
    )
    with pytest.raises(due.DueReservationRejected, match="retained due witness"):
        _reserve(store, original)
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        assert conn.execute("SELECT count(*) FROM due_reservations").fetchone() == (0,)


@pytest.mark.parametrize("tamper", ("count", "digest", "equal_digest"))
def test_committed_reservation_rejects_witness_mutation_during_receipt(
    tmp_path, monkeypatch, tamper,
):
    store, retained = _new(tmp_path)
    original = due.DueReservationReceipt

    def changed(*args):
        receipt = original(*args)
        witness = receipt.witness
        if tamper == "count":
            object.__setattr__(witness, "count", witness.count + 1)
        elif tamper == "digest":
            object.__setattr__(witness, "fingerprint", "f" * 64)
        else:
            value = witness.fingerprint
            replacement = "".join((value[:17], value[17:]))
            assert replacement == value and replacement is not value
            object.__setattr__(witness, "fingerprint", replacement)
        return receipt

    monkeypatch.setattr(due, "DueReservationReceipt", changed)
    with pytest.raises(due.DueReservationRejected, match="post-commit due witness changed"):
        _reserve(store, retained)
    # Row was already committed; a returned error does not mean rollback.
    assert store.witness().count == 1


def test_clean_due_receipt_still_survives_restart(tmp_path):
    store, retained = _new(tmp_path)
    receipt = _reserve(store, retained)
    reopened = due.DisconnectedDueReservations(tmp_path / "due.sqlite3")
    assert reopened.witness() == receipt.witness
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.witness.independent_custody_proven is False
