"""Detached due restart digest is pinned before any ledger read or reentrant hash."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations


@pytest.mark.parametrize("same_bytes", [True, False])
def test_rebound_review_domain_rejected_before_ledger_read(
    tmp_path, monkeypatch, same_bytes,
):
    ledger = DisconnectedDueReservations(tmp_path / "due.db")
    retained = ledger.witness()
    original = recovery._DOMAIN
    substitute = bytes(bytearray(original)) if same_bytes else original + b"changed"
    assert substitute is not original
    monkeypatch.setattr(recovery, "_DOMAIN", substitute)
    monkeypatch.setattr(
        ledger, "witness",
        lambda: pytest.fail("unsafe ledger read after review domain substitution"),
    )
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="digest authority changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


@pytest.mark.parametrize("callback", ["sha256", "dumps"])
def test_replaced_digest_callback_denied_before_ledger_read(
    tmp_path, monkeypatch, callback,
):
    ledger = DisconnectedDueReservations(tmp_path / "due.db")
    retained = ledger.witness()

    def forbidden(*args, **kwargs):
        pytest.fail("substituted digest callback executed")

    if callback == "sha256":
        monkeypatch.setattr(recovery.hashlib, "sha256", forbidden)
    else:
        monkeypatch.setattr(recovery.json, "dumps", forbidden)
    monkeypatch.setattr(
        ledger, "witness", lambda: pytest.fail("unsafe ledger witness read"),
    )
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="digest authority changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_prefix_callback_rebinding_review_domain_cannot_hash_result(
    tmp_path, monkeypatch,
):
    ledger = DisconnectedDueReservations(tmp_path / "due.db")
    retained = ledger.witness()
    original = recovery.review_retained_due_prefix

    def rebind(source, witness):
        reviewed = original(source, witness)
        monkeypatch.setattr(recovery, "_DOMAIN", bytes(bytearray(recovery._DOMAIN)))
        return reviewed

    monkeypatch.setattr(recovery, "review_retained_due_prefix", rebind)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="digest authority changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)
    assert ledger.witness() == retained


def test_unmodified_restart_remains_read_only_and_repeatable(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due.db")
    retained = ledger.witness()
    first = recovery.review_restarted_due_reservations(ledger, retained)
    second = recovery.review_restarted_due_reservations(ledger, retained)
    assert first == second
    assert first.status == "UNCHANGED_LOCAL_HISTORY"
    assert first.tool_dispatch_authorized is False
    assert first.notification_authorized is False
    assert first.automatic_replay_authorized is False
    assert ledger.witness() == retained
