"""Read-only restart bridge: durable quarantine prefix + next due preview.

This joins two disconnected fixtures without advancing a cursor, quarantining
a slot, starting a timer, notifying anyone, trusting caller time or dispatching
a ToolBackend. An internally coherent SQLite witness is not authenticated
external evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field

from .disconnected_schedule_preview import (
    DisconnectedDuePreview,
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)
from .disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineWitness,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
)

_DOMAIN = b"ARK-offline-schedule-resume-review-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DENIALS = (
    "trusted_clock_verified", "notification_authorized",
    "tool_execution_authorized", "automatic_replay_authorized",
    "consent_verified",
)


class ScheduleResumeRejected(ValueError):
    """A hypothetical restart cursor or quarantine prefix is not coherent."""


@dataclass(frozen=True, slots=True)
class OfflineScheduleResumeReview:
    quarantine_chain_sha256: str
    quarantined_count: int
    next_occurrence_id: str | None = field(repr=False)
    next_state: str
    preview_sha256: str
    review_sha256: str

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


def review_offline_schedule_resume(
    ledger: DisconnectedScheduleQuarantineLedger,
    policy: DisconnectedSchedulePolicy,
    cursor: DisconnectedScheduleCursor,
    *,
    retained_quarantine: QuarantineWitness,
    observed_now_ms: int,
) -> OfflineScheduleResumeReview:
    """Inspect a single prior quarantine prefix and its NEXT synthetic slot.

    A stale cursor cannot skip, revisit or reclassify an already-quarantined
    prefix. The caller must independently retain its witness across restarts.
    """
    if (
        type(ledger) is not DisconnectedScheduleQuarantineLedger
        or type(policy) is not DisconnectedSchedulePolicy
        or type(cursor) is not DisconnectedScheduleCursor
        or type(retained_quarantine) is not QuarantineWitness
        or type(observed_now_ms) is not int
        or not 0 <= observed_now_ms <= 2**63 - 1
    ):
        raise ScheduleResumeRejected("exact offline schedule resume inputs required")
    path_epoch, ledger_epoch = ledger._path, ledger._epoch
    policy_epoch = (
        policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
        policy.occurrence_count, policy.grace_ms,
    )
    cursor_epoch = (cursor.next_index, cursor.last_occurrence_id)
    witness_epoch = (
        retained_quarantine.count, retained_quarantine.chain_sha256,
    )

    def stable() -> None:
        if (
            type(ledger) is not DisconnectedScheduleQuarantineLedger
            or ledger._path is not path_epoch or ledger._epoch is not ledger_epoch
            or type(policy) is not DisconnectedSchedulePolicy
            or any(a is not b for a, b in zip((
                policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
                policy.occurrence_count, policy.grace_ms,
            ), policy_epoch, strict=True))
            or type(cursor) is not DisconnectedScheduleCursor
            or any(a is not b for a, b in zip((
                cursor.next_index, cursor.last_occurrence_id,
            ), cursor_epoch, strict=True))
            or type(retained_quarantine) is not QuarantineWitness
            or any(a is not b for a, b in zip((
                retained_quarantine.count, retained_quarantine.chain_sha256,
            ), witness_epoch, strict=True))
        ):
            raise ScheduleResumeRejected("offline schedule resume carrier changed")

    stable()
    if (
        ledger_epoch != policy_epoch
        or type(cursor.next_index) is not int
        or type(retained_quarantine.count) is not int
        or type(retained_quarantine.chain_sha256) is not str
        or _SHA.fullmatch(retained_quarantine.chain_sha256) is None
        or cursor.next_index != retained_quarantine.count
    ):
        raise ScheduleResumeRejected("quarantine prefix differs from restart cursor")
    if cursor.next_index > 0:
        previous = derive_quarantined_occurrence(
            QuarantinePolicy(*policy_epoch), cursor.next_index - 1,
        )
        if cursor.last_occurrence_id != previous:
            raise ScheduleResumeRejected("last quarantine identity differs from cursor")
    else:
        if cursor.last_occurrence_id is not None:
            raise ScheduleResumeRejected("non-genesis cursor without quarantines")
    try:
        first = ledger.inspect(retained=retained_quarantine)
        stable()
        if (
            type(first) is not QuarantineWitness
            or first != retained_quarantine
            or first.independently_authenticated is not False
        ):
            raise ScheduleResumeRejected("quarantine inspection gained authority")
        # A restart claim must not silently turn the caller clock backward
        # relative to a quarantine time already persisted in the local ledger.
        # Inspect the floor in a read-only transaction bracketed by the two
        # independently retained chain inspections. This detects regression;
        # it does NOT authenticate the caller's clock or authorize a slot.
        with closing(ledger._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            tail = (
                conn.execute(
                    "SELECT observed_ms FROM quarantines WHERE seq=?",
                    (retained_quarantine.count,),
                ).fetchone()
                if retained_quarantine.count else None
            )
            conn.rollback()
        stable()
        if retained_quarantine.count and (
            tail is None or len(tail) != 1 or type(tail[0]) is not int
            or not 0 <= tail[0] <= 2**63 - 1
        ):
            raise ScheduleResumeRejected("quarantine clock floor unavailable")
        if tail is not None and observed_now_ms < tail[0]:
            raise ScheduleResumeRejected("resume clock regressed below quarantine floor")
        preview = preview_disconnected_schedule(
            policy, cursor, observed_now_ms=observed_now_ms,
        )
        stable()
        if (
            type(preview) is not DisconnectedDuePreview
            or type(preview.state) is not str
            or preview.state not in (
                "NOT_DUE", "DUE_UNVERIFIED", "EXPIRED_QUARANTINE", "EXHAUSTED",
            )
            or preview.next_index != retained_quarantine.count
            or type(preview.fingerprint) is not str
            or _SHA.fullmatch(preview.fingerprint) is None
            or any(getattr(preview, key) is not False for key in _DENIALS)
        ):
            raise ScheduleResumeRejected("offline due preview gained authority")
        second = ledger.inspect(retained=retained_quarantine)
        stable()
        if type(second) is not QuarantineWitness or second != first:
            raise ScheduleResumeRejected("quarantine history changed during preview")
        fields = (
            retained_quarantine.chain_sha256, retained_quarantine.count,
            preview.occurrence_id, preview.state, preview.fingerprint,
        )
        encoded = json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode(
            "ascii"
        )
        digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
        output = OfflineScheduleResumeReview(*fields, digest)
        pinned = (
            output.quarantine_chain_sha256, output.quarantined_count,
            output.next_occurrence_id, output.next_state,
            output.preview_sha256, output.review_sha256,
        )
        descriptors = tuple(getattr(OfflineScheduleResumeReview, key) for key in _DENIALS)

        def stable_output() -> None:
            if (
                type(output) is not OfflineScheduleResumeReview
                or any(a is not b for a, b in zip((
                    output.quarantine_chain_sha256, output.quarantined_count,
                    output.next_occurrence_id, output.next_state,
                    output.preview_sha256, output.review_sha256,
                ), pinned, strict=True))
                or any(getattr(OfflineScheduleResumeReview, key) is not descriptor
                       for key, descriptor in zip(_DENIALS, descriptors, strict=True))
            ):
                raise ScheduleResumeRejected("offline resume witness changed")
            stable()

        stable_output()
        for key in _DENIALS:
            if getattr(output, key) is not False:
                raise ScheduleResumeRejected("offline resume gained authority")
            stable_output()
        last = ledger.inspect(retained=retained_quarantine)
        stable()
        stable_output()
        if type(last) is not QuarantineWitness or last != first:
            raise ScheduleResumeRejected("quarantine history changed after witness")
        return output
    except (ScheduleQuarantineRejected, SchedulePreviewRejected, sqlite3.Error) as exc:
        raise ScheduleResumeRejected("offline schedule resume verification rejected") from exc
