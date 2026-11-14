"""Restart due-witness class custody is checked before any injected getter.

All fixtures are local SQLite; no clock provenance, notification or Tool action.
"""

from __future__ import annotations

import subprocess
import sys

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
    "hook", ("__getattribute__", "__getattr__", "__init__"),
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


def test_inherited_new_allocation_poison_isolated_in_child_process():
    # Restoring object.__new__ through monkeypatch on a dataclass can leave
    # an explicit inherited __new__ on the class and poison all later tests.
    # Check the same rejection in a disposable interpreter instead.
    script = """
from pathlib import Path
from tempfile import TemporaryDirectory
from ark.agency import disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations, DueReservationWitness,
)
with TemporaryDirectory() as directory:
    ledger = DisconnectedDueReservations(Path(directory) / "due.sqlite")
    retained = ledger.witness()
    invoked = []
    def hostile(*args, **kwargs):
        invoked.append(True)
        raise AssertionError("forged allocation executed")
    DueReservationWitness.__new__ = staticmethod(hostile)
    try:
        recovery.review_restarted_due_reservations(ledger, retained)
    except recovery.DisconnectedDueRecoveryRejected as exc:
        assert "due witness carrier changed" in str(exc)
    else:
        raise AssertionError("forged witness allocation was accepted")
    assert invoked == []
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False, text=True, capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


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
