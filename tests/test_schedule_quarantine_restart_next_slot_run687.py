"""Restarted offline due previews remain bounded by stored quarantine prefix.

The caller supplies a synthetic clock and independently retained witness.
No preview or quarantine can authorize a notification, tool or automatic replay.
"""

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


def _case(tmp_path, count):
    sha = "a" * 64
    policy = DisconnectedSchedulePolicy(sha, 10_000, 5_000, 3, 500)
    quarantine = QuarantinePolicy(sha, 10_000, 5_000, 3, 500)
    path = tmp_path / "restart-quarantine.sqlite"
    writer = DisconnectedScheduleQuarantineLedger(
        path, policy=quarantine, create=True,
    )
    genesis = genesis_quarantine_witness(quarantine)
    latest = genesis
    last = None
    for index in range(count):
        last = derive_quarantined_occurrence(quarantine, index)
        latest = writer.quarantine_expired(
            index=index, occurrence_id=last,
            observed_ms=10_501 + 5_000 * index, retained=latest,
        ).witness
    cold = DisconnectedScheduleQuarantineLedger(path, policy=quarantine)
    assert cold.inspect(retained=latest) == latest
    return policy, quarantine, cold, genesis, latest, DisconnectedScheduleCursor(count, last)


@pytest.mark.parametrize(
    ("now", "expected"),
    ((10_501, "NOT_DUE"), (15_000, "DUE_UNVERIFIED"),
     (15_501, "EXPIRED_QUARANTINE")),
)
def test_one_slot_quarantined_then_restart_previews_next_without_authority(
    tmp_path, now, expected,
):
    policy, _quarantine, ledger, _genesis, retained, cursor = _case(tmp_path, 1)
    result = review_offline_schedule_resume(
        ledger, policy, cursor,
        retained_quarantine=retained, observed_now_ms=now,
    )
    assert result.next_state == expected
    assert result.quarantined_count == 1
    assert result.next_occurrence_id is not None
    assert ledger.inspect(retained=retained) == retained
    for name in (
        "trusted_clock_verified", "notification_authorized",
        "tool_execution_authorized", "automatic_replay_authorized",
        "consent_verified",
    ):
        assert getattr(result, name) is False


@pytest.mark.parametrize(
    ("now", "expected"),
    ((15_501, "NOT_DUE"), (20_000, "DUE_UNVERIFIED"),
     (20_501, "EXPIRED_QUARANTINE")),
)
def test_two_persisted_quarantines_cannot_revisit_prior_due_slots(
    tmp_path, now, expected,
):
    policy, _quarantine, ledger, _genesis, retained, cursor = _case(tmp_path, 2)
    result = review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=now,
    )
    assert result.next_state == expected
    assert result.quarantined_count == 2
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
    assert ledger.inspect(retained=retained) == retained


def test_all_quarantined_restart_is_exhausted_not_notification(tmp_path):
    policy, _quarantine, ledger, _genesis, retained, cursor = _case(tmp_path, 3)
    result = review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=20_501,
    )
    assert result.next_state == "EXHAUSTED"
    assert result.next_occurrence_id is None
    assert result.quarantined_count == 3
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False


def test_stale_restart_witness_cannot_reset_quarantine_prefix(tmp_path):
    policy, _quarantine, ledger, genesis, latest, _cursor = _case(tmp_path, 1)
    with pytest.raises(ScheduleResumeRejected, match="verification rejected"):
        review_offline_schedule_resume(
            ledger, policy, DisconnectedScheduleCursor(0),
            retained_quarantine=genesis, observed_now_ms=15_000,
        )
    assert ledger.inspect(retained=latest) == latest


def test_restart_clock_regression_below_persisted_floor_is_rejected(tmp_path):
    policy, _quarantine, ledger, _genesis, retained, cursor = _case(tmp_path, 1)
    with pytest.raises(ScheduleResumeRejected, match="regressed"):
        review_offline_schedule_resume(
            ledger, policy, cursor, retained_quarantine=retained,
            observed_now_ms=10_500,
        )
    assert ledger.inspect(retained=retained) == retained
