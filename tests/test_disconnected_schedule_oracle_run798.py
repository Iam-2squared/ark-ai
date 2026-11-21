"""Reference-oracle recurrence boundaries, hashes and quarantine semantics.

This oracle independently derives slot IDs and the preview digest. It makes
no clock, consent, notification or tool-dispatch authority claim.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from ark import disconnected_schedule_preview as schedule

_MAX = 2**63 - 1
_POLICY_SHA = "a" * 64
_DOMAIN = b"ARK-disconnected-schedule-preview-v1\0"
_CASES = (
    (0, 1_000, 0),
    (10_000, 60_000, 30_000),
    (1_000_000, 3_600_000, 60_000),
    (_MAX - 2_000, 1_000, 999),
)


def _slot(first, interval, index):
    due = first + index * interval
    payload = json.dumps(
        (_POLICY_SHA, index, due), ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    return "slot_" + hashlib.sha256(_DOMAIN + b"occurrence\0" + payload).hexdigest()


def _reference(first, interval, grace, index, now):
    policy = (_POLICY_SHA, first, interval, 3, grace)
    previous = None if index == 0 else _slot(first, interval, index - 1)
    cursor = (index, previous)
    if index == 3:
        state, slot, due = "EXHAUSTED", None, None
    else:
        due = first + index * interval
        slot = _slot(first, interval, index)
        if now < due:
            state = "NOT_DUE"
        elif now - due <= grace:
            state = "DUE_UNVERIFIED"
        else:
            state = "EXPIRED_QUARANTINE"
    payload = json.dumps(
        (policy, cursor, now, state, slot, due),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    fingerprint = hashlib.sha256(_DOMAIN + b"preview\0" + payload).hexdigest()
    return cursor, (state, slot, due, fingerprint)


def _cases():
    for first, interval, grace in _CASES:
        for index in range(4):
            due = first + index * interval
            offsets = (
                -interval - 1, -1, 0, grace, grace + 1, interval + grace,
            )
            for offset in offsets:
                now = max(0, min(_MAX, due + offset))
                yield first, interval, grace, index, now


@pytest.mark.parametrize("first,interval,grace,index,now", tuple(_cases()))
def test_independent_boundary_oracle_matches_exact_preview_and_digest(
    first, interval, grace, index, now,
):
    cursor, (state, slot, due, fingerprint) = _reference(
        first, interval, grace, index, now,
    )
    policy = schedule.DisconnectedSchedulePolicy(
        _POLICY_SHA, first, interval, 3, grace,
    )
    result = schedule.preview_disconnected_schedule(
        policy, schedule.DisconnectedScheduleCursor(*cursor),
        observed_now_ms=now,
    )
    assert result.state == state
    assert result.next_index == index
    assert result.occurrence_id == slot
    assert result.due_at_ms == due
    assert result.fingerprint == fingerprint
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False


@pytest.mark.parametrize("index", (0, 1, 2, 3))
@pytest.mark.parametrize("prior", (None, "slot_" + "f" * 64))
def test_forged_cursor_never_skips_or_claims_completion(index, prior):
    policy = schedule.DisconnectedSchedulePolicy(_POLICY_SHA, 10_000, 1_000, 3, 0)
    if (index == 0 and prior is None):
        # The one admissible genesis cursor is a regression control.
        report = schedule.preview_disconnected_schedule(
            policy, schedule.DisconnectedScheduleCursor(index, prior),
            observed_now_ms=10_000,
        )
        assert report.state == "DUE_UNVERIFIED"
    else:
        with pytest.raises(schedule.SchedulePreviewRejected):
            schedule.preview_disconnected_schedule(
                policy, schedule.DisconnectedScheduleCursor(index, prior),
                observed_now_ms=10_000,
            )


@pytest.mark.parametrize("now", (True, 1.0, -1, _MAX + 1, "10000"))
def test_nonexact_or_out_of_range_clock_refused(now):
    policy = schedule.DisconnectedSchedulePolicy(_POLICY_SHA, 10_000, 1_000, 3, 0)
    with pytest.raises(schedule.SchedulePreviewRejected):
        schedule.preview_disconnected_schedule(
            policy, schedule.DisconnectedScheduleCursor(0), observed_now_ms=now,
        )
