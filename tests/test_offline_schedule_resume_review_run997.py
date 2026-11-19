"""Run997: restart preview validates a retained quarantine prefix without advancing it."""

from __future__ import annotations

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)
from ark.offline_schedule_resume_review import (
    ScheduleResumeRejected,
    review_offline_schedule_resume,
)


def _fixture(tmp_path, quarantined_count: int = 1):
    quarantine_policy = QuarantinePolicy(
        policy_sha256="a" * 64,
        first_ms=10_000,
        interval_ms=5_000,
        count=3,
        grace_ms=500,
    )
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite3",
        policy=quarantine_policy,
        create=True,
    )
    witness = genesis_quarantine_witness(quarantine_policy)
    for index in range(quarantined_count):
        due = quarantine_policy.first_ms + index * quarantine_policy.interval_ms
        receipt = ledger.quarantine_expired(
            index=index,
            occurrence_id=derive_quarantined_occurrence(quarantine_policy, index),
            observed_ms=due + quarantine_policy.grace_ms + 1,
            retained=witness,
        )
        witness = receipt.witness

    policy = DisconnectedSchedulePolicy(
        policy_sha256=quarantine_policy.policy_sha256,
        first_due_at_ms=quarantine_policy.first_ms,
        interval_ms=quarantine_policy.interval_ms,
        occurrence_count=quarantine_policy.count,
        grace_ms=quarantine_policy.grace_ms,
    )
    cursor = DisconnectedScheduleCursor(
        next_index=quarantined_count,
        last_occurrence_id=(
            derive_quarantined_occurrence(quarantine_policy, quarantined_count - 1)
            if quarantined_count else None
        ),
    )
    return ledger, quarantine_policy, policy, cursor, witness


@pytest.mark.parametrize(
    ("quarantined_count", "observed_now_ms", "expected_state"),
    (
        (0, 9_999, "NOT_DUE"),
        (1, 15_000, "DUE_UNVERIFIED"),
        (1, 15_501, "EXPIRED_QUARANTINE"),
        (3, 20_501, "EXHAUSTED"),
    ),
)
def test_restart_review_classifies_next_slot_without_advancing_cursor_or_ledger(
    tmp_path, quarantined_count: int, observed_now_ms: int, expected_state: str,
):
    ledger, quarantine_policy, policy, cursor, witness = _fixture(
        tmp_path, quarantined_count,
    )
    cursor_before = (cursor.next_index, cursor.last_occurrence_id)

    review = review_offline_schedule_resume(
        ledger,
        policy,
        cursor,
        retained_quarantine=witness,
        observed_now_ms=observed_now_ms,
    )

    expected_occurrence = (
        None if quarantined_count == quarantine_policy.count
        else derive_quarantined_occurrence(quarantine_policy, quarantined_count)
    )
    assert review.quarantined_count == quarantined_count
    assert review.quarantine_chain_sha256 == witness.chain_sha256
    assert review.next_occurrence_id == expected_occurrence
    assert review.next_state == expected_state
    assert len(review.preview_sha256) == 64
    assert len(review.review_sha256) == 64
    assert cursor_before == (cursor.next_index, cursor.last_occurrence_id)
    assert ledger.inspect(retained=witness) == witness
    for name in (
        "trusted_clock_verified",
        "notification_authorized",
        "tool_execution_authorized",
        "automatic_replay_authorized",
        "consent_verified",
    ):
        assert getattr(review, name) is False
    assert witness.independently_authenticated is False


@pytest.mark.parametrize(
    "cursor",
    (
        DisconnectedScheduleCursor(0, None),
        DisconnectedScheduleCursor(1, "slot_" + "0" * 64),
    ),
)
def test_restart_review_rejects_cursor_not_bound_to_retained_prefix(tmp_path, cursor):
    ledger, _, policy, _, witness = _fixture(tmp_path, 1)
    with pytest.raises(ScheduleResumeRejected):
        review_offline_schedule_resume(
            ledger,
            policy,
            cursor,
            retained_quarantine=witness,
            observed_now_ms=15_000,
        )


def test_restart_review_rejects_clock_regression_below_quarantine_floor(tmp_path):
    ledger, _, policy, cursor, witness = _fixture(tmp_path, 1)
    with pytest.raises(ScheduleResumeRejected, match="regressed below quarantine floor"):
        review_offline_schedule_resume(
            ledger,
            policy,
            cursor,
            retained_quarantine=witness,
            observed_now_ms=10_500,
        )


def test_restart_review_rechecks_quarantine_after_preview_before_return(
    tmp_path, monkeypatch,
):
    ledger, quarantine_policy, policy, cursor, witness = _fixture(tmp_path, 1)
    original_inspect = ledger.inspect
    calls = []

    def append_new_expired_slot_after_first_inspection(*, retained):
        observed = original_inspect(retained=retained)
        calls.append(True)
        if len(calls) == 1:
            index = 1
            due = quarantine_policy.first_ms + index * quarantine_policy.interval_ms
            ledger.quarantine_expired(
                index=index,
                occurrence_id=derive_quarantined_occurrence(quarantine_policy, index),
                observed_ms=due + quarantine_policy.grace_ms + 1,
                retained=observed,
            )
        return observed

    monkeypatch.setattr(
        ledger, "inspect", append_new_expired_slot_after_first_inspection,
    )
    with pytest.raises(ScheduleResumeRejected):
        review_offline_schedule_resume(
            ledger,
            policy,
            cursor,
            retained_quarantine=witness,
            observed_now_ms=15_000,
        )
    assert len(calls) >= 2
