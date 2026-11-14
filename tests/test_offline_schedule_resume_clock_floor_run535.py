"""A detached schedule restart cannot regress below its durable quarantine clock."""

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


def _fixture(tmp_path, *, quarantines):
    policy = DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=qpolicy, create=True,
    )
    retained = genesis_quarantine_witness(qpolicy)
    last = None
    for index, observed in enumerate(quarantines):
        last = derive_quarantined_occurrence(qpolicy, index)
        retained = ledger.quarantine_expired(
            index=index, occurrence_id=last, observed_ms=observed,
            retained=retained,
        ).witness
    return ledger, policy, DisconnectedScheduleCursor(len(quarantines), last), retained


@pytest.mark.parametrize("now", (0, 999, 1199))
def test_single_quarantine_denies_time_regression(tmp_path, now):
    ledger, policy, cursor, retained = _fixture(tmp_path, quarantines=(1200,))
    with pytest.raises(ScheduleResumeRejected, match="clock regressed"):
        review_offline_schedule_resume(
            ledger, policy, cursor, retained_quarantine=retained,
            observed_now_ms=now,
        )
    assert ledger.inspect(retained=retained) == retained


@pytest.mark.parametrize("now", (1200, 1201, 1900))
def test_single_quarantine_accepts_equal_or_later_untrusted_clock(tmp_path, now):
    ledger, policy, cursor, retained = _fixture(tmp_path, quarantines=(1200,))
    result = review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=now,
    )
    assert result.quarantined_count == 1
    assert result.next_state == "NOT_DUE"
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("now,allowed", ((2200, False), (2201, True), (2202, True)))
def test_restart_clock_floor_uses_latest_quarantine(tmp_path, now, allowed):
    ledger, policy, cursor, retained = _fixture(
        tmp_path, quarantines=(1200, 2201),
    )
    if not allowed:
        with pytest.raises(ScheduleResumeRejected, match="clock regressed"):
            review_offline_schedule_resume(
                ledger, policy, cursor, retained_quarantine=retained,
                observed_now_ms=now,
            )
    else:
        result = review_offline_schedule_resume(
            ledger, policy, cursor, retained_quarantine=retained,
            observed_now_ms=now,
        )
        assert result.quarantined_count == 2
        assert result.tool_execution_authorized is False
        assert result.consent_verified is False


def test_genesis_has_no_prior_quarantine_clock_floor(tmp_path):
    ledger, policy, cursor, retained = _fixture(tmp_path, quarantines=())
    review = review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=retained,
        observed_now_ms=0,
    )
    assert review.next_state == "NOT_DUE"
    assert review.quarantined_count == 0
    assert review.automatic_replay_authorized is False
