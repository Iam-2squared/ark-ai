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
    with pytest.raises(
        due.DueReservationRejected,
        match=r"(?:retained due witness|witness authority)",
    ):
        _reserve(store, original)
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        assert conn.execute("SELECT count(*) FROM due_reservations").fetchone() == (0,)


@pytest.mark.parametrize("tamper", ("count", "digest", "equal_digest"))
def test_preinstalled_receipt_getter_cannot_tamper_with_due_witness(
    tmp_path, monkeypatch, tamper,
):
    store, retained = _new(tmp_path)
    original_getattribute = due.DueReservationReceipt.__getattribute__
    mutated = []

    def changed(self, name):
        value = original_getattribute(self, name)
        # This hostile getter must never run: the original receipt slot
        # contract is checked before SQLite reservation.
        if name == "witness" and not mutated:
            mutated.append(True)
            witness = value
            if tamper == "count":
                object.__setattr__(witness, "count", witness.count + 1)
            elif tamper == "digest":
                object.__setattr__(witness, "fingerprint", "f" * 64)
            else:
                fingerprint = witness.fingerprint
                replacement = "".join((fingerprint[:17], fingerprint[17:]))
                assert replacement == fingerprint and replacement is not fingerprint
                object.__setattr__(witness, "fingerprint", replacement)
        return value

    monkeypatch.setattr(due.DueReservationReceipt, "__getattribute__", changed)
    with pytest.raises(
        due.DueReservationRejected, match="due receipt constructor authority changed",
    ):
        _reserve(store, retained)
    assert mutated == []
    assert store.witness().count == 0


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
