"""Run949: proactive recurrence labels survive cold interpretation, not grants.

Only synthetic caller-supplied clocks and deterministic recurrence fixtures
are used. No timer, notification, persistence cursor or external action runs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)

_COLD = """
import json
import sys
from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    preview_disconnected_schedule,
)
p = DisconnectedSchedulePolicy(**json.loads(sys.argv[1]))
c = DisconnectedScheduleCursor(**json.loads(sys.argv[2]))
x = preview_disconnected_schedule(p, c, observed_now_ms=int(sys.argv[3]))
print(json.dumps({
    "state": x.state, "index": x.next_index,
    "occurrence": x.occurrence_id, "due": x.due_at_ms,
    "fingerprint": x.fingerprint,
    "trusted": x.trusted_clock_verified,
    "notice": x.notification_authorized,
    "tool": x.tool_execution_authorized,
    "replay": x.automatic_replay_authorized,
    "consent": x.consent_verified,
}, sort_keys=True))
"""


def _policy() -> DisconnectedSchedulePolicy:
    return DisconnectedSchedulePolicy("a" * 64, 1_000, 2_000, 3, 100)


@pytest.mark.parametrize(("now_ms", "expected"), (
    (999, "NOT_DUE"),
    (1_000, "DUE_UNVERIFIED"),
    (1_100, "DUE_UNVERIFIED"),
    (1_101, "EXPIRED_QUARANTINE"),
))
def test_cold_clock_boundary_has_stable_digest_without_execution(
    now_ms: int, expected: str,
) -> None:
    policy = _policy()
    cursor = DisconnectedScheduleCursor(0)
    preview = preview_disconnected_schedule(
        policy, cursor, observed_now_ms=now_ms,
    )
    assert preview.state == expected
    cold = subprocess.run(
        [sys.executable, "-c", _COLD,
         json.dumps(asdict(policy), sort_keys=True),
         json.dumps(asdict(cursor), sort_keys=True), str(now_ms)],
        capture_output=True, text=True, check=True, timeout=20,
    )
    report = json.loads(cold.stdout)
    assert report == {
        "state": expected,
        "index": 0,
        "occurrence": preview.occurrence_id,
        "due": 1_000,
        "fingerprint": preview.fingerprint,
        "trusted": False,
        "notice": False,
        "tool": False,
        "replay": False,
        "consent": False,
    }


@pytest.mark.parametrize("now_ms", (3_000, 3_100, 3_101))
def test_cursor_advances_only_with_matching_previous_occurrence(
    now_ms: int,
) -> None:
    policy = _policy()
    first = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(0), observed_now_ms=1_000,
    )
    second_cursor = DisconnectedScheduleCursor(1, first.occurrence_id)
    second = preview_disconnected_schedule(
        policy, second_cursor, observed_now_ms=now_ms,
    )
    assert second.state == (
        "DUE_UNVERIFIED" if now_ms <= 3_100 else "EXPIRED_QUARANTINE"
    )
    assert second.occurrence_id != first.occurrence_id
    assert second.notification_authorized is False
    assert second.tool_execution_authorized is False
    assert second.automatic_replay_authorized is False
    with pytest.raises(SchedulePreviewRejected):
        preview_disconnected_schedule(
            DisconnectedSchedulePolicy("b" * 64, 1_000, 2_000, 3, 100),
            second_cursor, observed_now_ms=now_ms,
        )


def test_exhausted_cursor_is_not_a_grant_to_reschedule() -> None:
    policy = _policy()
    first = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(0), observed_now_ms=1_000,
    )
    second = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(1, first.occurrence_id),
        observed_now_ms=3_000,
    )
    third = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(2, second.occurrence_id),
        observed_now_ms=5_000,
    )
    exhausted = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(3, third.occurrence_id),
        observed_now_ms=10_000,
    )
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.occurrence_id is None
    assert exhausted.due_at_ms is None
    assert exhausted.notification_authorized is False
    assert exhausted.tool_execution_authorized is False


@pytest.mark.parametrize("bad_now", (True, False, -1, 2**63))
def test_caller_clock_is_exact_and_bounded(bad_now: object) -> None:
    with pytest.raises(SchedulePreviewRejected):
        preview_disconnected_schedule(
            _policy(), DisconnectedScheduleCursor(0),
            observed_now_ms=bad_now,
        )
