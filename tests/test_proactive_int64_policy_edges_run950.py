"""Run950: synthetic proactive recurrence arithmetic never wraps SQLite int64.

The clock, policy and cursor are caller assertions, not trusted time,
durable schedule completion or permission for notifications/tool execution.
"""

from __future__ import annotations

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)

_MAX = 2**63 - 1
_YEAR_MS = 366 * 24 * 60 * 60 * 1000


@pytest.mark.parametrize(("first", "interval", "count", "grace"), (
    (_MAX - 999, 1_000, 2, 0),  # Last due overflows int64.
    (_MAX + 1, 1_000, 1, 0),
    (0, 0, 1, 0),
    (0, 1_000, 0, 0),
    (0, 1_000, 4_097, 0),
    (0, 1_000, 1, 1_000),
    (0, 62_000, 1, 60_001),
    (0, _YEAR_MS + 1, 1, 0),
))
def test_invalid_policy_limits_denied_before_preview_identity(
    first: int, interval: int, count: int, grace: int,
) -> None:
    policy = DisconnectedSchedulePolicy(
        "a" * 64, first, interval, count, grace,
    )
    with pytest.raises(SchedulePreviewRejected):
        preview_disconnected_schedule(
            policy, DisconnectedScheduleCursor(0), observed_now_ms=0,
        )


@pytest.mark.parametrize(("now_ms", "state"), (
    (_MAX - 1, "NOT_DUE"),
    (_MAX, "DUE_UNVERIFIED"),
))
def test_terminal_int64_occurrence_is_still_inert(
    now_ms: int, state: str,
) -> None:
    policy = DisconnectedSchedulePolicy(
        "a" * 64, _MAX - 1_000, 1_000, 2, 0,
    )
    first = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(0),
        observed_now_ms=_MAX - 1_000,
    )
    assert first.state == "DUE_UNVERIFIED"
    second = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(1, first.occurrence_id),
        observed_now_ms=now_ms,
    )
    assert second.state == state
    assert second.due_at_ms == _MAX
    assert second.occurrence_id != first.occurrence_id
    assert second.trusted_clock_verified is False
    assert second.notification_authorized is False
    assert second.tool_execution_authorized is False
    assert second.automatic_replay_authorized is False
    assert second.consent_verified is False
    exhausted = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(2, second.occurrence_id),
        observed_now_ms=_MAX,
    )
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.occurrence_id is None
    assert exhausted.tool_execution_authorized is False
