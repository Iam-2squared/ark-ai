"""Disconnected proactive terminal/cursor policy boundary regressions.

No real scheduler, timer, trusted clock, consent or tool backend. Everything
here is a synthetic, caller-asserted and explicitly non-authorizing preview.
"""

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)


def _policy(**changes):
    args = dict(
        policy_sha256="a" * 64,
        first_due_at_ms=1_000,
        interval_ms=1_000,
        occurrence_count=3,
        grace_ms=50,
    )
    args.update(changes)
    return DisconnectedSchedulePolicy(**args)


def _review(policy, cursor, now):
    result = preview_disconnected_schedule(
        policy, cursor, observed_now_ms=now,
    )
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False
    return result


def test_exhausted_cursor_remains_terminal_on_restart_and_different_clock():
    policy = _policy()
    first = _review(policy, DisconnectedScheduleCursor(0), 1_000)
    second = _review(
        policy, DisconnectedScheduleCursor(1, first.occurrence_id), 2_000,
    )
    third = _review(
        policy, DisconnectedScheduleCursor(2, second.occurrence_id), 3_000,
    )
    final_cursor = DisconnectedScheduleCursor(3, third.occurrence_id)
    last = _review(policy, final_cursor, 2**63 - 1)
    restart = _review(policy, final_cursor, 0)
    assert last.state == restart.state == "EXHAUSTED"
    assert last.next_index == restart.next_index == 3
    assert last.occurrence_id is restart.occurrence_id is None
    assert last.due_at_ms is restart.due_at_ms is None
    assert last.fingerprint != restart.fingerprint
    # The terminal index itself is not evidence that any of the three
    # external effects ran, nor an invitation to schedule an extra slot.


@pytest.mark.parametrize(
    "cursor",
    [
        DisconnectedScheduleCursor(0, "slot_" + "0" * 64),
        DisconnectedScheduleCursor(1, None),
        DisconnectedScheduleCursor(1, "slot_" + "0" * 64),
        DisconnectedScheduleCursor(1, "slot_" + "0" * 63),
        DisconnectedScheduleCursor(1, "slot_" + "G" * 64),
        DisconnectedScheduleCursor(4, None),
        DisconnectedScheduleCursor(True, None),
    ],
)
def test_untrusted_cursor_never_recovers_from_bogus_or_advanced_identity(cursor):
    with pytest.raises(SchedulePreviewRejected):
        _review(_policy(), cursor, 5_000)


def test_valid_prior_occurrence_from_other_policy_cannot_be_replayed():
    first_policy = _policy(policy_sha256="a" * 64)
    other_policy = _policy(policy_sha256="b" * 64)
    prior = _review(first_policy, DisconnectedScheduleCursor(0), 1_000)
    with pytest.raises(SchedulePreviewRejected, match="prior occurrence"):
        _review(
            other_policy,
            DisconnectedScheduleCursor(1, prior.occurrence_id),
            2_000,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"policy_sha256": "A" * 64},
        {"first_due_at_ms": True},
        {"interval_ms": 999},
        {"occurrence_count": 0},
        {"occurrence_count": 4_097},
        {"grace_ms": 1_000},
        {"first_due_at_ms": 2**63 - 1, "occurrence_count": 2},
        {"interval_ms": 366 * 24 * 60 * 60 * 1_000 + 1},
    ],
)
def test_bounded_recurrence_validation_fail_closed(changes):
    with pytest.raises(SchedulePreviewRejected):
        _review(_policy(**changes), DisconnectedScheduleCursor(0), 1_000)


def test_last_representable_slot_does_not_wrap_or_schedule_a_fourth_slot():
    policy = _policy(
        first_due_at_ms=2**63 - 1 - 2_000,
        interval_ms=1_000,
        occurrence_count=3,
        grace_ms=50,
    )
    first = _review(policy, DisconnectedScheduleCursor(0), 2**63 - 1)
    assert first.state == "EXPIRED_QUARANTINE"
    assert first.due_at_ms == 2**63 - 1 - 2_000
    assert first.next_index == 0
    # No arithmetic rollover, auto-catch-up or success claim even at max clock.
    second = _review(
        policy, DisconnectedScheduleCursor(1, first.occurrence_id), 2**63 - 1,
    )
    third = _review(
        policy, DisconnectedScheduleCursor(2, second.occurrence_id), 2**63 - 1,
    )
    assert third.state == "DUE_UNVERIFIED"
    assert third.due_at_ms == 2**63 - 1
    assert third.next_index == 2
