"""Bounded offline recurrence previews for synthetic proactive scheduling.

There is no OS clock, timer, notification, Tool execution, or durable cursor
storage. Every clock and cursor is caller asserted. A due label cannot grant
consent, a trusted time source, or permission to repeat an external effect.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OCCURRENCE = re.compile(r"slot_[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-schedule-preview-v1\0"
_MAX_MS = 2**63 - 1
_MAX_COUNT = 4096
_MAX_INTERVAL_MS = 366 * 24 * 60 * 60 * 1000
_MAX_GRACE_MS = 60_000


class SchedulePreviewRejected(ValueError):
    """An offline schedule, cursor, or caller time is invalid or inconsistent."""


@dataclass(frozen=True, slots=True)
class DisconnectedSchedulePolicy:
    policy_sha256: str
    first_due_at_ms: int
    interval_ms: int
    occurrence_count: int
    grace_ms: int


@dataclass(frozen=True, slots=True)
class DisconnectedScheduleCursor:
    next_index: int
    last_occurrence_id: str | None = None


@dataclass(frozen=True, slots=True)
class DisconnectedDuePreview:
    state: str
    next_index: int
    occurrence_id: str | None = field(repr=False)
    due_at_ms: int | None
    fingerprint: str

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


def _valid_policy(policy: object) -> None:
    if type(policy) is not DisconnectedSchedulePolicy:
        raise SchedulePreviewRejected("exact synthetic schedule policy required")
    sha, first, interval, count, grace = (
        policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
        policy.occurrence_count, policy.grace_ms,
    )
    if (
        type(sha) is not str or _SHA.fullmatch(sha) is None
        or any(type(n) is not int for n in (first, interval, count, grace))
        or not 0 <= first <= _MAX_MS
        or not 1_000 <= interval <= _MAX_INTERVAL_MS
        or not 1 <= count <= _MAX_COUNT
        or not 0 <= grace <= min(interval - 1, _MAX_GRACE_MS)
        or first + (count - 1) * interval > _MAX_MS
    ):
        raise SchedulePreviewRejected("invalid bounded recurrence or policy identity")


def _occurrence(policy: DisconnectedSchedulePolicy, index: int) -> str:
    due = policy.first_due_at_ms + index * policy.interval_ms
    payload = json.dumps(
        (policy.policy_sha256, index, due), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return "slot_" + hashlib.sha256(_DOMAIN + b"occurrence\0" + payload).hexdigest()


def preview_disconnected_schedule(
    policy: DisconnectedSchedulePolicy,
    cursor: DisconnectedScheduleCursor,
    *,
    observed_now_ms: int,
) -> DisconnectedDuePreview:
    """Classify exactly the next claimed occurrence, never silently skip it.

    Lateness beyond the grace window is QUARANTINED, not advanced. The
    previous occurrence identity only checks internal consistency of a
    caller-owned cursor, not durable custody or authenticated completion.
    """
    _valid_policy(policy)
    if type(cursor) is not DisconnectedScheduleCursor:
        raise SchedulePreviewRejected("exact synthetic schedule cursor required")
    if type(observed_now_ms) is not int or not 0 <= observed_now_ms <= _MAX_MS:
        raise SchedulePreviewRejected("invalid caller-asserted clock")
    original_policy = (
        policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
        policy.occurrence_count, policy.grace_ms,
    )
    original_cursor = (cursor.next_index, cursor.last_occurrence_id)
    carriers = original_policy + original_cursor

    def assert_epoch() -> None:
        if (
            type(policy) is not DisconnectedSchedulePolicy
            or type(cursor) is not DisconnectedScheduleCursor
            or (policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
                policy.occurrence_count, policy.grace_ms) != original_policy
            or (cursor.next_index, cursor.last_occurrence_id) != original_cursor
            or any(
                current is not saved for current, saved in zip(
                    (policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
                     policy.occurrence_count, policy.grace_ms,
                     cursor.next_index, cursor.last_occurrence_id),
                    carriers, strict=True,
                )
            )
        ):
            raise SchedulePreviewRejected("schedule input changed during preview")

    assert_epoch()
    index = cursor.next_index
    if type(index) is not int or not 0 <= index <= policy.occurrence_count:
        raise SchedulePreviewRejected("invalid schedule cursor index")
    previous = cursor.last_occurrence_id
    if index == 0:
        if previous is not None:
            raise SchedulePreviewRejected("genesis cursor cannot claim prior occurrence")
    elif (
        type(previous) is not str or _OCCURRENCE.fullmatch(previous) is None
        or previous != _occurrence(policy, index - 1)
    ):
        raise SchedulePreviewRejected("cursor prior occurrence does not match policy")
    assert_epoch()
    if index == policy.occurrence_count:
        state, occurrence, due = "EXHAUSTED", None, None
    else:
        due = policy.first_due_at_ms + index * policy.interval_ms
        occurrence = _occurrence(policy, index)
        if observed_now_ms < due:
            state = "NOT_DUE"
        elif observed_now_ms - due <= policy.grace_ms:
            state = "DUE_UNVERIFIED"
        else:
            state = "EXPIRED_QUARANTINE"
    packed = json.dumps(
        (original_policy, original_cursor, observed_now_ms, state,
         occurrence, due), separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    fingerprint = hashlib.sha256(_DOMAIN + b"preview\0" + packed).hexdigest()
    assert_epoch()
    result = DisconnectedDuePreview(state, index, occurrence, due, fingerprint)
    assert_epoch()
    if (
        type(result) is not DisconnectedDuePreview
        or (result.state, result.next_index, result.occurrence_id,
            result.due_at_ms, result.fingerprint)
        != (state, index, occurrence, due, fingerprint)
        or result.state is not state or result.occurrence_id is not occurrence
        or result.fingerprint is not fingerprint
    ):
        raise SchedulePreviewRejected("constructed preview carrier changed")
    return result
