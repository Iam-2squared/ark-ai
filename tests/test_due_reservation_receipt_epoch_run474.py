"""Detached SQLite due receipts are inert and retain original witness carriers."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_reservation as due


def _ledger(tmp_path):
    ledger = due.DisconnectedDueReservations(tmp_path / "due.sqlite3")
    return ledger, ledger.witness()


def _reserve(ledger, retained):
    return ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=100,
        observed_now_ms=101, retained=retained,
    )


def test_forged_post_commit_receipt_does_not_claim_authority(tmp_path, monkeypatch):
    ledger, original = _ledger(tmp_path)

    class Forged:
        execution_authorized = True
        notification_authorized = True
        automatic_replay_authorized = True
        trusted_clock_verified = True

    monkeypatch.setattr(due, "DueReservationReceipt", lambda *args: Forged())
    with pytest.raises(due.DueReservationRejected, match="constructed due reservation"):
        _reserve(ledger, original)
    # A failed post-commit diagnostic is not evidence of a rolled-back row.
    assert ledger.witness().count == 1


@pytest.mark.parametrize("field", ("occurrence_id",))
def test_equal_valued_receipt_carrier_replacement_rejected(
    tmp_path, monkeypatch, field,
):
    ledger, original_witness = _ledger(tmp_path)
    original_type = due.DueReservationReceipt

    def forged(*args):
        receipt = original_type(*args)
        original = getattr(receipt, field)
        changed = "".join((original[:9], original[9:]))
        assert changed == original and changed is not original
        object.__setattr__(receipt, field, changed)
        return receipt

    monkeypatch.setattr(due, "DueReservationReceipt", forged)
    with pytest.raises(due.DueReservationRejected, match="constructed due reservation"):
        _reserve(ledger, original_witness)
    assert ledger.witness().count == 1


@pytest.mark.parametrize("mutation", ("equal_hash", "float_count"))
def test_retained_witness_replacement_during_read_denied(
    tmp_path, monkeypatch, mutation,
):
    ledger, retained = _ledger(tmp_path)
    original_inspect = due._inspect

    def altered(conn):
        result = original_inspect(conn)
        if mutation == "equal_hash":
            fingerprint = retained.fingerprint
            replacement = "".join((fingerprint[:16], fingerprint[16:]))
            assert replacement == fingerprint and replacement is not fingerprint
            object.__setattr__(retained, "fingerprint", replacement)
        else:
            object.__setattr__(retained, "count", 0.0)
        return result

    monkeypatch.setattr(due, "_inspect", altered)
    with pytest.raises(due.DueReservationRejected, match="retained due custody"):
        _reserve(ledger, retained)
    assert ledger.witness().count == 0


def test_genesis_witness_constructor_cannot_forge_custody(monkeypatch):
    original = due.DueReservationWitness

    def altered(count, fingerprint):
        result = original(count, fingerprint)
        replacement = "".join((fingerprint[:12], fingerprint[12:]))
        assert fingerprint == replacement and fingerprint is not replacement
        object.__setattr__(result, "fingerprint", replacement)
        return result

    monkeypatch.setattr(due, "DueReservationWitness", altered)
    with pytest.raises(due.DueReservationRejected, match="constructed due witness"):
        due.genesis_due_witness()


def test_valid_detached_reservation_still_survives_restart(tmp_path):
    ledger, origin = _ledger(tmp_path)
    receipt = _reserve(ledger, origin)
    restarted = due.DisconnectedDueReservations(tmp_path / "due.sqlite3")
    assert restarted.witness() == receipt.witness
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    with pytest.raises(due.DueReservationRejected):
        _reserve(restarted, origin)
