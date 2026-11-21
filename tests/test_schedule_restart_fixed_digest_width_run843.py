"""Offline recurrence restart labels are bounded before protocol regex checks.

All schedule inputs are synthetic and no notification or tool operation runs.
"""

from __future__ import annotations

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)


def _policy(sha: str = "a" * 64) -> DisconnectedSchedulePolicy:
    return DisconnectedSchedulePolicy(sha, 10_000, 1_000, 3, 200)


@pytest.mark.parametrize(
    "digest", ("a" * 63, "a" * 65, "a" * 120_000, "A" * 64),
)
def test_oversized_or_noncanonical_policy_digest_is_rejected(digest: str) -> None:
    with pytest.raises(SchedulePreviewRejected, match="recurrence"):
        preview_disconnected_schedule(
            _policy(digest), DisconnectedScheduleCursor(0),
            observed_now_ms=10_000,
        )


@pytest.mark.parametrize(
    "previous", (
        "slot_" + "a" * 63,
        "slot_" + "a" * 65,
        "slot_" + "a" * 120_000,
        "slot_" + "A" * 64,
    ),
)
def test_untrusted_restart_cursor_is_rejected(previous: str) -> None:
    with pytest.raises(SchedulePreviewRejected, match="prior occurrence"):
        preview_disconnected_schedule(
            _policy(), DisconnectedScheduleCursor(1, previous),
            observed_now_ms=11_000,
        )


def test_exact_length_cursor_retains_denial_only_semantics() -> None:
    policy = _policy()
    first = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(0), observed_now_ms=10_000,
    )
    assert first.state == "DUE_UNVERIFIED"
    assert len(first.occurrence_id or "") == 69
    second = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(1, first.occurrence_id),
        observed_now_ms=11_000,
    )
    assert second.state == "DUE_UNVERIFIED"
    assert second.trusted_clock_verified is False
    assert second.notification_authorized is False
    assert second.tool_execution_authorized is False
    assert second.automatic_replay_authorized is False
