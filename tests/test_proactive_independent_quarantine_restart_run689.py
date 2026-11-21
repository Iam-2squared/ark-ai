"""Independent offline trigger schedules do not inherit each other's veto.

One retained quarantine prefix cannot silently advance a disjoint trigger's
cursor across a restart. Even a locally due preview has no notification or
execution authority; clocks and schedule IDs are synthetic only.
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
from ark.offline_schedule_resume_review import review_offline_schedule_resume


@pytest.mark.parametrize(
    ("now_ms", "first_expected"),
    ((11_000, "NOT_DUE"), (15_000, "DUE_UNVERIFIED"),
     (15_501, "EXPIRED_QUARANTINE")),
)
def test_one_trigger_quarantine_does_not_advance_another_trigger(
    tmp_path, now_ms, first_expected,
):
    first_digest, second_digest = "a" * 64, "b" * 64
    first_policy = DisconnectedSchedulePolicy(first_digest, 10_000, 5_000, 3, 500)
    second_policy = DisconnectedSchedulePolicy(second_digest, 10_000, 5_000, 3, 500)
    first_quarantine = QuarantinePolicy(first_digest, 10_000, 5_000, 3, 500)
    second_quarantine = QuarantinePolicy(second_digest, 10_000, 5_000, 3, 500)
    first_path = tmp_path / "first.sqlite"
    second_path = tmp_path / "second.sqlite"
    first = DisconnectedScheduleQuarantineLedger(
        first_path, policy=first_quarantine, create=True,
    )
    DisconnectedScheduleQuarantineLedger(
        second_path, policy=second_quarantine, create=True,
    )
    first_genesis = genesis_quarantine_witness(first_quarantine)
    second_genesis = genesis_quarantine_witness(second_quarantine)
    first_occurrence = derive_quarantined_occurrence(first_quarantine, 0)
    first_retained = first.quarantine_expired(
        index=0, occurrence_id=first_occurrence, observed_ms=10_501,
        retained=first_genesis,
    ).witness
    cold_first = DisconnectedScheduleQuarantineLedger(
        first_path, policy=first_quarantine,
    )
    cold_second = DisconnectedScheduleQuarantineLedger(
        second_path, policy=second_quarantine,
    )
    first_result = review_offline_schedule_resume(
        cold_first, first_policy, DisconnectedScheduleCursor(1, first_occurrence),
        retained_quarantine=first_retained, observed_now_ms=now_ms,
    )
    second_result = review_offline_schedule_resume(
        cold_second, second_policy, DisconnectedScheduleCursor(0),
        retained_quarantine=second_genesis, observed_now_ms=now_ms,
    )
    assert first_result.next_state == first_expected
    assert second_result.next_state == "EXPIRED_QUARANTINE"
    assert first_result.quarantined_count == 1
    assert second_result.quarantined_count == 0
    assert cold_first.inspect(retained=first_retained) == first_retained
    assert cold_second.inspect(retained=second_genesis) == second_genesis
    for result in (first_result, second_result):
        assert result.trusted_clock_verified is False
        assert result.notification_authorized is False
        assert result.tool_execution_authorized is False
        assert result.automatic_replay_authorized is False
        assert result.consent_verified is False
