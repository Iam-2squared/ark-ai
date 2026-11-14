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

# Pin the diagnostic protocol before the caller's private recurrence,
# opaque policy digest or asserted clock reaches JSON/SHA callbacks.
# These checks detect local instrumentation, not trusted provenance.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_SHA = _SHA
_ORIGINAL_OCCURRENCE = _OCCURRENCE
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_BOUNDS = (_MAX_MS, _MAX_COUNT, _MAX_INTERVAL_MS, _MAX_GRACE_MS)


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


# A reentrant synthetic constructor must not replace an inert result class
# with a compatible-looking object that advertises authority.
_POLICY_TYPE = DisconnectedSchedulePolicy
_CURSOR_TYPE = DisconnectedScheduleCursor
_RESULT_TYPE = DisconnectedDuePreview
_DENIAL_NAMES = (
    "trusted_clock_verified", "notification_authorized",
    "tool_execution_authorized", "automatic_replay_authorized",
    "consent_verified",
)
_ORIGINAL_DENIAL_DESCRIPTORS = tuple(
    vars(_RESULT_TYPE)[key] for key in _DENIAL_NAMES
)
# Inert schedule input and output dataclasses are only frozen per instance.
# A substituted exact-class slot, __new__, or getter can run BEFORE the
# ordinary input type checks or the False-only result getters. Capture the
# import-original class dictionaries for all three carriers.
_CARRIER_FIELDS = (
    (_POLICY_TYPE, (
        "policy_sha256", "first_due_at_ms", "interval_ms",
        "occurrence_count", "grace_ms",
    )),
    (_CURSOR_TYPE, ("next_index", "last_occurrence_id")),
    (_RESULT_TYPE, (
        "state", "next_index", "occurrence_id", "due_at_ms", "fingerprint",
    )),
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_CARRIER_DESCRIPTORS = tuple(
    tuple(vars(kind).get(name) for name in (*fields, *_CARRIER_HOOKS))
    for kind, fields in _CARRIER_FIELDS
)


def _require_original_denials() -> None:
    # Pin all three constructors, not only the result's False properties.
    # A rebound input type may accept a counterfeit object, and a rebound
    # result constructor can execute code before postconstruction validation.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _SHA is not _ORIGINAL_SHA
        or _OCCURRENCE is not _ORIGINAL_OCCURRENCE
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or any(type(value) is not int for value in
               (_MAX_MS, _MAX_COUNT, _MAX_INTERVAL_MS, _MAX_GRACE_MS))
        or (_MAX_MS, _MAX_COUNT, _MAX_INTERVAL_MS, _MAX_GRACE_MS)
           != _ORIGINAL_BOUNDS
        or DisconnectedSchedulePolicy is not _POLICY_TYPE
        or DisconnectedScheduleCursor is not _CURSOR_TYPE
        or DisconnectedDuePreview is not _RESULT_TYPE
        or any(
            vars(kind).get(name) is not original
            for (kind, fields), saved in zip(
                _CARRIER_FIELDS, _ORIGINAL_CARRIER_DESCRIPTORS, strict=True,
            )
            for name, original in zip(
                (*fields, *_CARRIER_HOOKS), saved, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(key) is not original
            for key, original in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise SchedulePreviewRejected("constructed preview carrier changed")


def _valid_policy(policy: object) -> None:
    if type(policy) is not DisconnectedSchedulePolicy:
        raise SchedulePreviewRejected("exact synthetic schedule policy required")
    sha, first, interval, count, grace = (
        policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
        policy.occurrence_count, policy.grace_ms,
    )
    # Reject oversized persisted policy labels before regex scanning.
    if (
        type(sha) is not str or len(sha) != 64
        or _SHA.fullmatch(sha) is None
        or any(type(n) is not int for n in (first, interval, count, grace))
        or not 0 <= first <= _MAX_MS
        or not 1_000 <= interval <= _MAX_INTERVAL_MS
        or not 1 <= count <= _MAX_COUNT
        or not 0 <= grace <= min(interval - 1, _MAX_GRACE_MS)
        or first + (count - 1) * interval > _MAX_MS
    ):
        raise SchedulePreviewRejected("invalid bounded recurrence or policy identity")


def _occurrence(policy: DisconnectedSchedulePolicy, index: int) -> str:
    _require_original_denials()
    due = policy.first_due_at_ms + index * policy.interval_ms
    payload = json.dumps(
        (policy.policy_sha256, index, due), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    _require_original_denials()
    digest = hashlib.sha256(_DOMAIN + b"occurrence\0" + payload).hexdigest()
    _require_original_denials()
    return "slot_" + digest


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
    # Denial getters are executable callbacks; reject substitutions before
    # processing any synthetic recurrence or caller clock.
    _require_original_denials()
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
        _require_original_denials()
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
    # A cursor may be replayed from an untrusted restart snapshot; width
    # is a fixed protocol invariant, not just a regex acceptance property.
    elif (
        type(previous) is not str or len(previous) != 69
        or _OCCURRENCE.fullmatch(previous) is None
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
    assert_epoch()
    fingerprint = hashlib.sha256(_DOMAIN + b"preview\0" + packed).hexdigest()
    assert_epoch()
    result = _RESULT_TYPE(state, index, occurrence, due, fingerprint)

    def stable_result() -> None:
        _require_original_denials()
        # Even a False property may rewrite an EARLIER authority descriptor.
        # Bind all descriptor objects as well as the exact returned fields.
        if (
            type(result) is not _RESULT_TYPE
            or type(result.state) is not str
            or type(result.next_index) is not int
            or type(result.fingerprint) is not str
            or (result.occurrence_id is not None
                and type(result.occurrence_id) is not str)
            or (result.due_at_ms is not None
                and type(result.due_at_ms) is not int)
            or result.state is not state
            or result.next_index is not index
            or result.occurrence_id is not occurrence
            or result.due_at_ms is not due
            or result.fingerprint is not fingerprint
            or any(
                vars(_RESULT_TYPE).get(name) is not descriptor
                for name, descriptor in zip(
                    _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
                )
            )
        ):
            raise SchedulePreviewRejected("constructed preview carrier changed")

    assert_epoch()
    stable_result()
    for name in _DENIAL_NAMES:
        if getattr(result, name) is not False:
            raise SchedulePreviewRejected("constructed preview carrier changed")
        assert_epoch()
        stable_result()
    # The caller-supplied clock is not trusted and this is never a dispatch.
    assert_epoch()
    stable_result()
    return result
