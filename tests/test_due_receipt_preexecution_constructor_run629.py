"""Synthetic due reservation never runs a swapped receipt constructor.

Only disposable SQLite fixtures are used. A rejected post-insert transition
must not be misreported as proof of a completed external action.
"""

import pytest

from ark.agency import disconnected_due_reservation as due

_POLICY = "a" * 64


def _case(tmp_path):
    store = due.DisconnectedDueReservations(tmp_path / "due-slots.sqlite")
    return store, store.witness()


def _reserve(store, witness):
    return store.reserve_due(
        policy_sha256=_POLICY,
        due_at_ms=1_000,
        observed_now_ms=1_001,
        retained=witness,
    )


@pytest.mark.parametrize("method", ("__init__", "__post_init__"))
def test_preinstalled_receipt_hook_is_never_invoked(tmp_path, monkeypatch, method):
    store, witness = _case(tmp_path)
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("hostile synthetic receipt hook executed")

    monkeypatch.setattr(due.DueReservationReceipt, method, hostile, raising=False)
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        _reserve(store, witness)
    assert executed == []
    assert store.witness() == witness


def test_swapped_receipt_class_is_rejected_before_reserving(tmp_path, monkeypatch):
    store, witness = _case(tmp_path)
    executed = []

    def counterfeit(*args):
        executed.append(args)
        raise AssertionError("counterfeit receipt callable ran")

    monkeypatch.setattr(due, "DueReservationReceipt", counterfeit)
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        _reserve(store, witness)
    assert executed == []
    assert store.witness() == witness


@pytest.mark.parametrize(
    "name", ("execution_authorized", "notification_authorized"),
)
def test_preinstalled_receipt_authority_getter_is_never_invoked(
    tmp_path, monkeypatch, name,
):
    store, witness = _case(tmp_path)
    executed = []

    def hostile(instance):
        executed.append(instance)
        raise AssertionError("counterfeit authority getter ran")

    monkeypatch.setattr(due.DueReservationReceipt, name, property(hostile))
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        _reserve(store, witness)
    assert executed == []
    assert store.witness() == witness


def test_post_insert_digest_injection_rolls_back_and_never_calls_forged_receipt(
    tmp_path, monkeypatch,
):
    store, witness = _case(tmp_path)
    executed = []
    injected = []
    original_digest = due._digest

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("forged receipt initializer executed")

    def reentrant_digest(rows):
        result = original_digest(rows)
        if len(rows) == 1 and not injected:
            injected.append(True)
            monkeypatch.setattr(due.DueReservationReceipt, "__init__", hostile)
        return result

    monkeypatch.setattr(due, "_digest", reentrant_digest)
    with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
        _reserve(store, witness)
    assert injected == [True]
    assert executed == []
    assert store.witness() == witness


def test_unmodified_due_receipt_is_inert_and_persisted_across_restart(tmp_path):
    store, initial = _case(tmp_path)
    receipt = _reserve(store, initial)
    assert receipt.witness.count == 1
    assert store.witness() == receipt.witness
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    reopened = due.DisconnectedDueReservations.reopen_with_witness(
        store._path, retained=receipt.witness,
    )
    assert reopened.witness() == receipt.witness
