"""Cold-interpreter schedule fingerprints and terminal boundary evidence.

These are caller-asserted synthetic timestamps: no OS timer, notification,
consent, trusted clock, external effect, or authorization to replay a slot.
"""

from __future__ import annotations

from multiprocessing import get_context
from queue import Empty

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)


def _policy(digest="a" * 64):
    return DisconnectedSchedulePolicy(
        digest, first_due_at_ms=1000, interval_ms=1000,
        occurrence_count=3, grace_ms=50,
    )


def _snapshot(policy, cursor, now):
    result = preview_disconnected_schedule(
        policy, cursor, observed_now_ms=now,
    )
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False
    return (
        result.state, result.next_index, result.occurrence_id,
        result.due_at_ms, result.fingerprint,
    )


def _cold_snapshot(policy, cursor, now, queue):
    try:
        queue.put(("ok", _snapshot(policy, cursor, now)))
    except Exception as exc:
        queue.put(("error", type(exc).__name__, str(exc)))


@pytest.mark.parametrize(
    ("index", "now", "state"),
    (
        (0, 1000, "DUE_UNVERIFIED"),
        (1, 1999, "NOT_DUE"),
        (1, 2051, "EXPIRED_QUARANTINE"),
        (3, 4000, "EXHAUSTED"),
    ),
)
def test_cold_interpreter_keeps_occurrence_and_fingerprint_exact(
    index, now, state,
):
    policy = _policy()
    previous = None
    for i in range(index):
        previous = preview_disconnected_schedule(
            policy, DisconnectedScheduleCursor(i, previous),
            observed_now_ms=1000 + i * 1000,
        ).occurrence_id
    cursor = DisconnectedScheduleCursor(index, previous)
    baseline = _snapshot(policy, cursor, now)
    assert baseline[0] == state

    context = get_context("spawn")
    messages = context.Queue()
    child = context.Process(
        target=_cold_snapshot, args=(policy, cursor, now, messages),
    )
    try:
        child.start()
        outcome = messages.get(timeout=35)
    except Empty as exc:
        pytest.fail(f"offline schedule child did not answer: {exc}")
    finally:
        child.join(timeout=20)
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)
        messages.close()
        messages.join_thread()

    assert child.exitcode == 0
    assert outcome == ("ok", baseline)


def test_prior_slot_cannot_be_reused_after_policy_retargeting():
    old = _policy("a" * 64)
    new = _policy("b" * 64)
    first = preview_disconnected_schedule(
        old, DisconnectedScheduleCursor(0), observed_now_ms=1000,
    )
    assert first.occurrence_id is not None
    with pytest.raises(
        SchedulePreviewRejected, match="prior occurrence",
    ):
        preview_disconnected_schedule(
            new, DisconnectedScheduleCursor(1, first.occurrence_id),
            observed_now_ms=2000,
        )


def test_sqlite_integer_clock_endpoint_has_no_wraparound_or_dispatch():
    limit = 2**63 - 1
    policy = DisconnectedSchedulePolicy(
        "f" * 64, first_due_at_ms=limit - 2000,
        interval_ms=1000, occurrence_count=3, grace_ms=0,
    )
    previous = None
    for index in range(3):
        result = preview_disconnected_schedule(
            policy, DisconnectedScheduleCursor(index, previous),
            observed_now_ms=limit - 2000 + index * 1000,
        )
        assert result.state == "DUE_UNVERIFIED"
        assert result.due_at_ms == limit - 2000 + index * 1000
        assert result.notification_authorized is False
        previous = result.occurrence_id
    exhausted = preview_disconnected_schedule(
        policy, DisconnectedScheduleCursor(3, previous),
        observed_now_ms=limit,
    )
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.occurrence_id is None
    assert exhausted.notification_authorized is False

    overflow = DisconnectedSchedulePolicy(
        "f" * 64, first_due_at_ms=limit - 1999,
        interval_ms=1000, occurrence_count=3, grace_ms=0,
    )
    with pytest.raises(SchedulePreviewRejected, match="invalid bounded"):
        preview_disconnected_schedule(
            overflow, DisconnectedScheduleCursor(0),
            observed_now_ms=limit,
        )
