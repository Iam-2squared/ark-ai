"""Disconnected proactive clock boundaries never authorize catch-up or replay.

Synthetic asserted timestamps only; no OS timer, notification or tool backend.
"""

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    preview_disconnected_schedule,
)


def _policy():
    return DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 50)


def _preview(now, *, cursor=None):
    return preview_disconnected_schedule(
        _policy(), cursor or DisconnectedScheduleCursor(0),
        observed_now_ms=now,
    )


def _all_denied(result):
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False


def test_grace_boundary_uses_exact_next_occurrence_with_no_automatic_advance():
    before = _preview(999)
    exact = _preview(1000)
    last_grace_ms = _preview(1050)
    overdue = _preview(1051)
    assert [r.state for r in (before, exact, last_grace_ms, overdue)] == [
        "NOT_DUE", "DUE_UNVERIFIED", "DUE_UNVERIFIED", "EXPIRED_QUARANTINE",
    ]
    assert {r.next_index for r in (before, exact, last_grace_ms, overdue)} == {0}
    assert len({r.occurrence_id for r in
                (before, exact, last_grace_ms, overdue)}) == 1
    assert {r.due_at_ms for r in
            (before, exact, last_grace_ms, overdue)} == {1000}
    for result in (before, exact, last_grace_ms, overdue):
        _all_denied(result)


def test_overdue_restart_still_points_to_same_slot_without_auto_replay():
    first = _preview(20_000)
    restarted = _preview(20_000, cursor=DisconnectedScheduleCursor(0))
    assert first == restarted
    assert first.state == "EXPIRED_QUARANTINE"
    assert first.next_index == 0
    assert first.occurrence_id.startswith("slot_")
    _all_denied(restarted)


def test_caller_asserted_advanced_cursor_does_not_prove_completion():
    first = _preview(1000)
    second = _preview(
        3000, cursor=DisconnectedScheduleCursor(
            next_index=1, last_occurrence_id=first.occurrence_id,
        ),
    )
    assert second.state == "EXPIRED_QUARANTINE"
    assert second.next_index == 1
    assert second.due_at_ms == 2000
    assert second.occurrence_id != first.occurrence_id
    _all_denied(second)
