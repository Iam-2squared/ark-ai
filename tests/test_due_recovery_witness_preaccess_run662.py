"""Restart due-witness class custody is checked before any injected getter.

All fixtures are local SQLite; no clock provenance, notification or Tool action.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
)


def _fixture(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due-restart.sqlite")
    return ledger, ledger.witness()


@pytest.mark.parametrize("field", ("count", "fingerprint"))
def test_preinstalled_witness_slot_poison_rejected_before_read(
    tmp_path, monkeypatch, field,
):
    ledger, retained = _fixture(tmp_path)
    executed = []

    class Poison:
        def __get__(self, instance, owner):
            executed.append(field)
            raise AssertionError("untrusted witness slot getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(DueReservationWitness, field, Poison())
        patch.setattr(
            ledger, "witness",
            lambda: pytest.fail("ledger read occurred after witness slot drift"),
        )
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected,
            match="due witness carrier changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert executed == []


@pytest.mark.parametrize(
    "hook", ("__getattribute__", "__getattr__", "__new__", "__init__"),
)
def test_witness_lookup_or_allocation_hook_rejected_before_read(
    tmp_path, monkeypatch, hook,
):
    ledger, retained = _fixture(tmp_path)
    executed = []

    def hostile(*args, **kwargs):
        executed.append(hook)
        raise AssertionError("untrusted witness lookup or allocation executed")

    with monkeypatch.context() as patch:
        patch.setattr(DueReservationWitness, hook, hostile, raising=False)
        patch.setattr(
            ledger, "witness",
            lambda: pytest.fail("ledger read occurred after witness hook drift"),
        )
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected,
            match="due witness carrier changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert executed == []


def test_false_looking_custody_override_rejected_without_invocation(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    invoked = []

    def forged(self):
        invoked.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            DueReservationWitness, "independent_custody_proven",
            property(forged),
        )
        patch.setattr(
            ledger, "witness",
            lambda: pytest.fail("ledger read occurred after denial drift"),
        )
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected,
            match="due witness carrier changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert invoked == []


def test_child_witness_slot_change_after_first_check_denied(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    actual_read = ledger.witness
    invoked = []

    class Poison:
        def __get__(self, instance, owner):
            invoked.append(True)
            raise AssertionError("post-observation slot getter executed")

    def changed_witness():
        observed = actual_read()
        monkeypatch.setattr(DueReservationWitness, "fingerprint", Poison())
        return observed

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "witness", changed_witness)
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected,
            match="due witness carrier changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert invoked == []


def test_unmodified_witness_remains_passive_and_repeatable(tmp_path):
    ledger, retained = _fixture(tmp_path)
    first = recovery.review_restarted_due_reservations(ledger, retained)
    second = recovery.review_restarted_due_reservations(ledger, retained)
    assert first == second
    assert first.status == "UNCHANGED_LOCAL_HISTORY"
    assert all(getattr(first, flag) is False for flag in recovery._RESULT_DENIALS)
