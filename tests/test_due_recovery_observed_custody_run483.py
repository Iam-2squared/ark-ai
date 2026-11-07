"""Synthetic due-restart review must retain the observed witness across callbacks."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations


@pytest.mark.parametrize("phase", ["json", "hash", "result"])
@pytest.mark.parametrize("field", ["fingerprint", "count"])
def test_observed_witness_callback_mutation_rejected(tmp_path, monkeypatch, phase, field):
    ledger = DisconnectedDueReservations(tmp_path / "due.sqlite3")
    retained = ledger.witness()
    observed = ledger.witness()
    monkeypatch.setattr(ledger, "witness", lambda: observed)

    def corrupt():
        new = "f" * 64 if field == "fingerprint" else 1
        object.__setattr__(observed, field, new)

    if phase == "json":
        original = recovery.json.dumps

        def injected(*args, **kwargs):
            value = original(*args, **kwargs)
            corrupt()
            return value

        monkeypatch.setattr(recovery.json, "dumps", injected)
    elif phase == "hash":
        original = recovery.hashlib.sha256

        def injected(*args, **kwargs):
            digest = original(*args, **kwargs)
            corrupt()
            return digest

        monkeypatch.setattr(recovery.hashlib, "sha256", injected)
    else:
        original = recovery.DisconnectedDueRecoveryReview

        def injected(*args, **kwargs):
            result = original(*args, **kwargs)
            corrupt()
            return result

        monkeypatch.setattr(recovery, "DisconnectedDueRecoveryReview", injected)

    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="observed due witness changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_unmodified_observed_witness_remains_denial_only(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due.sqlite3")
    retained = ledger.witness()
    result = recovery.review_restarted_due_reservations(ledger, retained)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert not result.historical_prefix_proven
    assert not result.independently_custodied
    assert not result.trusted_clock_verified
    assert not result.notification_authorized
    assert not result.tool_dispatch_authorized
    assert not result.automatic_replay_authorized
