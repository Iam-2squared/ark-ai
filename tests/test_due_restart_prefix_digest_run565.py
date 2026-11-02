"""Due-slot restart receipts commit to the verified local prefix review."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_prefix_review import review_retained_due_prefix
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations


def _case(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due-prefix-receipt.sqlite3")
    first = ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=1_000,
        observed_now_ms=1_001, retained=ledger.witness(),
    )
    return ledger, first.witness


def test_restart_digest_includes_local_prefix_review_fingerprint(tmp_path):
    ledger, retained = _case(tmp_path)
    prefix = review_retained_due_prefix(ledger, retained)
    receipt = recovery.review_restarted_due_reservations(ledger, retained)
    payload = (
        (retained.count, retained.fingerprint),
        (retained.count, retained.fingerprint),
        "UNCHANGED_LOCAL_HISTORY", prefix.review_sha256,
    )
    expected = hashlib.sha256(
        recovery._DOMAIN
        + json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    ).hexdigest()
    assert receipt.digest == expected
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False


@pytest.mark.parametrize("bad", ("bad", "", "A" * 64))
def test_malformed_prefix_receipt_is_rejected_before_return(
    monkeypatch, tmp_path, bad,
):
    ledger, retained = _case(tmp_path)
    original = recovery.review_retained_due_prefix

    def bad_prefix(*args, **kwargs):
        return replace(original(*args, **kwargs), review_sha256=bad)

    monkeypatch.setattr(recovery, "review_retained_due_prefix", bad_prefix)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="prefix result changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_matching_tip_but_changed_prefix_receipt_changes_digest(
    monkeypatch, tmp_path,
):
    ledger, retained = _case(tmp_path)
    normal = recovery.review_restarted_due_reservations(ledger, retained)
    original = recovery.review_retained_due_prefix

    def forged_receipt(*args, **kwargs):
        result = original(*args, **kwargs)
        return replace(result, review_sha256="f" * 64)

    # Synthetic monkeypatches demonstrate *binding*, not authentication.
    monkeypatch.setattr(recovery, "review_retained_due_prefix", forged_receipt)
    altered = recovery.review_restarted_due_reservations(ledger, retained)
    assert altered.digest != normal.digest
    assert altered.historical_prefix_proven is False
    assert altered.tool_dispatch_authorized is False
