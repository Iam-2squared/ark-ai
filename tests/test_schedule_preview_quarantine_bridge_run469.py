"""Offline schedule previews and durable expired-slot quarantine use one identity.

All clocks and retained witnesses are caller supplied. These fixtures provide
no notification, tool execution, consent, or authenticated-clock authority.
"""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as preview_module
from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_POLICY = "a" * 64


def _policies():
    preview = DisconnectedSchedulePolicy(_POLICY, 10_000, 5_000, 3, 500)
    quarantine = QuarantinePolicy(_POLICY, 10_000, 5_000, 3, 500)
    return preview, quarantine


def test_expired_preview_ids_persist_in_order_across_restart(tmp_path):
    preview_policy, quarantine_policy = _policies()
    path = tmp_path / "offline-quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=quarantine_policy, create=True,
    )
    witness = genesis_quarantine_witness(quarantine_policy)
    cursor = DisconnectedScheduleCursor(0)
    for index in range(3):
        observed = 10_501 + index * 5_000
        review = preview_disconnected_schedule(
            preview_policy, cursor, observed_now_ms=observed,
        )
        assert review.state == "EXPIRED_QUARANTINE"
        assert review.next_index == index
        assert review.occurrence_id == derive_quarantined_occurrence(
            quarantine_policy, index,
        )
        receipt = ledger.quarantine_expired(
            index=index, occurrence_id=review.occurrence_id,
            observed_ms=observed, retained=witness,
        )
        assert receipt.quarantined_index == index
        assert receipt.execution_authorized is False
        assert receipt.notification_authorized is False
        assert receipt.trusted_clock_verified is False
        assert review.tool_execution_authorized is False
        witness = receipt.witness
        cursor = DisconnectedScheduleCursor(index + 1, review.occurrence_id)
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=quarantine_policy)
    assert reopened.inspect(retained=witness) == witness
    exhausted = preview_disconnected_schedule(
        preview_policy, cursor, observed_now_ms=30_000,
    )
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.occurrence_id is None
    assert witness.independently_authenticated is False


def test_nonexpired_preview_cannot_be_persisted_as_expired(tmp_path):
    preview_policy, quarantine_policy = _policies()
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.db", policy=quarantine_policy, create=True,
    )
    before = genesis_quarantine_witness(quarantine_policy)
    review = preview_disconnected_schedule(
        preview_policy, DisconnectedScheduleCursor(0), observed_now_ms=10_500,
    )
    assert review.state == "DUE_UNVERIFIED"
    with pytest.raises(ScheduleQuarantineRejected, match="not expired"):
        ledger.quarantine_expired(
            index=0, occurrence_id=review.occurrence_id,
            observed_ms=10_500, retained=before,
        )
    assert ledger.inspect(retained=before) == before


def test_restart_requires_separately_retained_latest_witness(tmp_path):
    preview_policy, quarantine_policy = _policies()
    path = tmp_path / "quarantine.db"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=quarantine_policy, create=True,
    )
    genesis = genesis_quarantine_witness(quarantine_policy)
    review = preview_disconnected_schedule(
        preview_policy, DisconnectedScheduleCursor(0), observed_now_ms=10_501,
    )
    current = ledger.quarantine_expired(
        index=0, occurrence_id=review.occurrence_id,
        observed_ms=10_501, retained=genesis,
    ).witness
    reloaded = DisconnectedScheduleQuarantineLedger(path, policy=quarantine_policy)
    with pytest.raises(ScheduleQuarantineRejected, match="stale"):
        reloaded.inspect(retained=genesis)
    assert reloaded.inspect(retained=current) == current


def test_preview_identity_of_other_policy_is_rejected_by_quarantine(tmp_path):
    preview_policy, quarantine_policy = _policies()
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.db", policy=quarantine_policy, create=True,
    )
    other = DisconnectedSchedulePolicy(
        "b" * 64, preview_policy.first_due_at_ms, preview_policy.interval_ms,
        preview_policy.occurrence_count, preview_policy.grace_ms,
    )
    review = preview_disconnected_schedule(
        other, DisconnectedScheduleCursor(0), observed_now_ms=10_501,
    )
    with pytest.raises(ScheduleQuarantineRejected, match="policy-bound"):
        ledger.quarantine_expired(
            index=0, occurrence_id=review.occurrence_id,
            observed_ms=10_501, retained=genesis_quarantine_witness(quarantine_policy),
        )


def test_forged_preview_result_subclass_cannot_claim_execution(monkeypatch):
    original = preview_module.DisconnectedDuePreview

    class ForgedPreview(original):
        @property
        def tool_execution_authorized(self) -> bool:
            return True

    monkeypatch.setattr(preview_module, "DisconnectedDuePreview", ForgedPreview)
    policy, _ = _policies()
    with pytest.raises(SchedulePreviewRejected, match="constructed preview"):
        preview_disconnected_schedule(
            policy, DisconnectedScheduleCursor(0), observed_now_ms=10_501,
        )
