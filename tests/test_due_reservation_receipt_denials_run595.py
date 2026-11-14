"""Synthetic due receipts cannot gain authority before or after COMMIT.

Reservations are local deduplication markers, not dispatch or notifications.
A failed post-COMMIT validation never implies rollback or safe automatic retry.
"""

import pytest

import ark.agency.disconnected_due_reservation as due


def _reserve(tmp_path):
    ledger = due.DisconnectedDueReservations(tmp_path / "receipt-denial.sqlite")

    def submit():
        return ledger.reserve_due(
            policy_sha256="a" * 64,
            due_at_ms=100,
            observed_now_ms=101,
            retained=due.genesis_due_witness(),
        )

    return ledger, submit


@pytest.mark.parametrize("name", due._RECEIPT_DENIALS)
def test_false_only_replacement_is_not_original_receipt_authority(tmp_path, monkeypatch, name):
    ledger, submit = _reserve(tmp_path)
    monkeypatch.setattr(due.DueReservationReceipt, name, property(lambda _: False))
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        submit()
    assert ledger.witness().count == 0


@pytest.mark.parametrize("name", due._RECEIPT_DENIALS)
def test_true_receipt_authority_is_rejected_before_local_commit(tmp_path, monkeypatch, name):
    ledger, submit = _reserve(tmp_path)
    monkeypatch.setattr(due.DueReservationReceipt, name, property(lambda _: True))
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        submit()
    assert ledger.witness().count == 0


def test_last_getter_cannot_replace_previously_checked_descriptor(tmp_path, monkeypatch):
    ledger, submit = _reserve(tmp_path)
    receipt_type = due.DueReservationReceipt
    original_getattribute = receipt_type.__getattribute__

    def drift(self, name):
        value = original_getattribute(self, name)
        if name == "trusted_clock_verified":
            monkeypatch.setattr(
                receipt_type, "execution_authorized", property(lambda _: False),
            )
        return value

    monkeypatch.setattr(receipt_type, "__getattribute__", drift)
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        submit()
    # The substituted getter must be rejected BEFORE any reservation.
    assert ledger.witness().count == 0


def test_last_getter_cannot_replace_equal_receipt_identifier(tmp_path, monkeypatch):
    ledger, submit = _reserve(tmp_path)
    receipt_type = due.DueReservationReceipt
    original_getattribute = receipt_type.__getattribute__

    def drift(self, name):
        value = original_getattribute(self, name)
        if name == "trusted_clock_verified":
            original = original_getattribute(self, "occurrence_id")
            replacement = ("!" + original)[1:]
            assert replacement == original and replacement is not original
            object.__setattr__(self, "occurrence_id", replacement)
        return value

    monkeypatch.setattr(receipt_type, "__getattribute__", drift)
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        submit()
    assert ledger.witness().count == 0


def test_unmodified_receipt_remains_inert_and_restart_readable(tmp_path):
    ledger, submit = _reserve(tmp_path)
    receipt = submit()
    assert type(receipt) is due.DueReservationReceipt
    for name in due._RECEIPT_DENIALS:
        assert getattr(receipt, name) is False
    assert receipt.witness == ledger.witness()
