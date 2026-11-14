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
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


def _require_original_schedule_review_codec() -> None:
    """Keep synthetic recurrence hashing code fixed across review callbacks."""
    if (
        _SHA is not _ORIGINAL_SHA_PATTERN
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise ScheduleResumeRejected("offline resume digest or grammar authority changed")


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


# Rebound result constructors are executable, so reject a substituted class
# before any ledger read instead of trusting only denial-property identities.
_RESULT_TYPE = OfflineScheduleResumeReview
_ORIGINAL_RESUME_INIT = vars(_RESULT_TYPE)["__init__"]
_RESULT_FIELDS = (
    "quarantine_chain_sha256", "quarantined_count", "next_occurrence_id",
    "next_state", "preview_sha256", "review_sha256",
)
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT_TYPE)[key] for key in _RESULT_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT_TYPE).get(key) for key in _RESULT_HOOKS
)


def _require_original_result_carriers() -> None:
    _require_original_schedule_review_codec()
    # Even a denied-only result can have executable slot or lookup hooks.
    # Reject those substitutions before touching the independent SQLite
    # history or evaluating caller-provided recurrence carriers.
    if (
        OfflineScheduleResumeReview is not _RESULT_TYPE
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESUME_INIT
        or any(
            vars(_RESULT_TYPE).get(key) is not original
            for key, original in zip(
                _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(key) is not original
            for key, original in zip(
                _RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS, strict=True,
            )
        )
    ):
        raise ScheduleResumeRejected(
            "offline resume result carrier changed: denial descriptor replaced"
        )
    # Check denial-only authority surfaces before reading ledger paths,
    # cursor fields or retained private scheduling history. A getter returning
    # False is still executable code if installed later.
    if any(
        vars(_RESULT_TYPE).get(name) is not original
        for name, original in zip(_DENIALS, _ORIGINAL_RESUME_DENIALS, strict=True)
    ):
        raise ScheduleResumeRejected(
            "offline resume witness changed: denial descriptor replaced"
        )
    if (
        vars(QuarantineWitness).get("independently_authenticated")
        is not _ORIGINAL_QUARANTINE_DENIAL
    ):
        raise ScheduleResumeRejected(
            "quarantine witness authority descriptor changed"
        )
    if any(
        vars(DisconnectedDuePreview).get(name) is not original
        for name, original in zip(_DENIALS, _ORIGINAL_PREVIEW_DENIALS, strict=True)
    ):
        raise ScheduleResumeRejected("offline preview denial descriptor changed")


# Import-time denial descriptors: capturing them after a ledger/preview
# callback would legitimize a replacement False getter as a new baseline.
_ORIGINAL_QUARANTINE_DENIAL = vars(QuarantineWitness)["independently_authenticated"]
_ORIGINAL_PREVIEW_DENIALS = tuple(
    vars(DisconnectedDuePreview)[name] for name in _DENIALS
)
_ORIGINAL_RESUME_DENIALS = tuple(
    vars(_RESULT_TYPE)[name] for name in _DENIALS
)


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
    _require_original_result_carriers()
    path_epoch, ledger_epoch = ledger._path, ledger._epoch
    policy_epoch = (
        policy.policy_sha256, policy.first_due_at_ms, policy.interval_ms,
        policy.occurrence_count, policy.grace_ms,
    )
    cursor_epoch = (cursor.next_index, cursor.last_occurrence_id)
    witness_epoch = (
        retained_quarantine.count, retained_quarantine.chain_sha256,
    )
    # Quarantine reports are diagnostic only. A late ledger.inspect callback
    # must not rebind their False-only authority property, even to another
    # getter returning False; the final read has no authenticated actor.
    quarantine_denial = _ORIGINAL_QUARANTINE_DENIAL

    def denied_quarantine(candidate: QuarantineWitness) -> None:
        if type(candidate) is not QuarantineWitness:
            raise ScheduleResumeRejected("quarantine witness type changed")
        pinned = (candidate.count, candidate.chain_sha256)
        if (
            vars(QuarantineWitness).get("independently_authenticated")
            is not quarantine_denial
            or candidate.independently_authenticated is not False
            or any(current is not original for current, original in zip(
                (candidate.count, candidate.chain_sha256), pinned, strict=True,
            ))
            or vars(QuarantineWitness).get("independently_authenticated")
            is not quarantine_denial
        ):
            raise ScheduleResumeRejected("quarantine witness gained authority or changed")

    def stable() -> None:
        _require_original_result_carriers()
        # The final diagnostic result is denial-only. Pin original class
        # descriptors at import time, before any SQLite/preview callbacks.
        if (
            OfflineScheduleResumeReview is not _RESULT_TYPE
            or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESUME_INIT
            or any(
                vars(_RESULT_TYPE).get(name) is not original
                for name, original in zip(
                    _DENIALS, _ORIGINAL_RESUME_DENIALS, strict=True,
                )
            )
        ):
            raise ScheduleResumeRejected(
                "offline resume witness changed: denial descriptor replaced"
            )
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
        if vars(QuarantineWitness).get("independently_authenticated") is not quarantine_denial:
            raise ScheduleResumeRejected(
                "quarantine witness authority descriptor changed"
            )
        if any(
            vars(DisconnectedDuePreview).get(name) is not original
            for name, original in zip(
                _DENIALS, _ORIGINAL_PREVIEW_DENIALS, strict=True,
            )
        ):
            raise ScheduleResumeRejected(
                "offline preview denial descriptor changed"
            )

    # Never use the replaceable dataclass __eq__ when determining whether
    # the three independently read quarantine witnesses match the retained
    # prefix. A patched True equality could conceal a forged/stale callback.
    def same_witness(candidate: QuarantineWitness, expected: QuarantineWitness) -> bool:
        return (
            type(candidate) is QuarantineWitness
            and type(candidate.count) is int
            and type(candidate.chain_sha256) is str
            and candidate.count == expected.count
            and candidate.chain_sha256 == expected.chain_sha256
        )

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
        denied_quarantine(first)
        stable()
        if not same_witness(first, retained_quarantine):
            raise ScheduleResumeRejected("quarantine inspection differs from retained")
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
            or type(preview.next_index) is not int
            or preview.next_index != retained_quarantine.count
            or (preview.occurrence_id is not None
                and type(preview.occurrence_id) is not str)
            or (preview.due_at_ms is not None
                and type(preview.due_at_ms) is not int)
            or type(preview.fingerprint) is not str
            or _SHA.fullmatch(preview.fingerprint) is None
            or any(getattr(preview, key) is not False for key in _DENIALS)
        ):
            raise ScheduleResumeRejected("offline due preview gained authority")
        # A callback may return an exact-class, denied-only preview that
        # nevertheless lies about a slot or its due classification. Recompute
        # the next occurrence independently of the preview implementation.
        if cursor.next_index == policy.occurrence_count:
            expected_occurrence, expected_due, expected_state = (
                None, None, "EXHAUSTED",
            )
        else:
            expected_occurrence = derive_quarantined_occurrence(
                QuarantinePolicy(*policy_epoch), cursor.next_index,
            )
            expected_due = (
                policy.first_due_at_ms + cursor.next_index * policy.interval_ms
            )
            if observed_now_ms < expected_due:
                expected_state = "NOT_DUE"
            elif observed_now_ms - expected_due <= policy.grace_ms:
                expected_state = "DUE_UNVERIFIED"
            else:
                expected_state = "EXPIRED_QUARANTINE"
        if (
            preview.occurrence_id != expected_occurrence
            or preview.due_at_ms != expected_due
            or preview.state != expected_state
        ):
            raise ScheduleResumeRejected("offline preview differs from recurrence")
        # A caller-replaced preview can lie about its digest while preserving
        # every visible slot field. Recompute the preview's own fingerprint
        # from the original policy/cursor/time, not from the preview callback.
        preview_payload = json.dumps(
            (policy_epoch, cursor_epoch, observed_now_ms, expected_state,
             expected_occurrence, expected_due),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        stable()
        expected_fingerprint = hashlib.sha256(
            b"ARK-disconnected-schedule-preview-v1\0"
            + b"preview\0" + preview_payload
        ).hexdigest()
        stable()
        if preview.fingerprint != expected_fingerprint:
            raise ScheduleResumeRejected("offline preview fingerprint disagrees with inputs")
        preview_epoch = (
            preview.state, preview.next_index, preview.occurrence_id,
            preview.due_at_ms, preview.fingerprint,
        )
        preview_descriptors = _ORIGINAL_PREVIEW_DENIALS

        def stable_preview() -> None:
            if (
                type(preview) is not DisconnectedDuePreview
                or any(current is not original for current, original in zip((
                    preview.state, preview.next_index, preview.occurrence_id,
                    preview.due_at_ms, preview.fingerprint,
                ), preview_epoch, strict=True))
                or any(vars(DisconnectedDuePreview).get(key) is not original
                       for key, original in zip(_DENIALS, preview_descriptors, strict=True))
            ):
                raise ScheduleResumeRejected("offline preview changed after validation")

        stable_preview()
        second = ledger.inspect(retained=retained_quarantine)
        denied_quarantine(second)
        stable_preview()
        stable()
        if not same_witness(second, retained_quarantine):
            raise ScheduleResumeRejected("quarantine history changed during preview")
        fields = (
            retained_quarantine.chain_sha256, retained_quarantine.count,
            preview.occurrence_id, preview.state, preview.fingerprint,
        )
        encoded = json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode(
            "ascii"
        )
        stable()
        digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
        stable()
        # Refuse an initializer replaced during preview/ledger/hash callbacks,
        # before executing any injected result-construction code.
        stable()
        output = _RESULT_TYPE(*fields, digest)
        stable()
        pinned = (
            output.quarantine_chain_sha256, output.quarantined_count,
            output.next_occurrence_id, output.next_state,
            output.preview_sha256, output.review_sha256,
        )
        descriptors = _ORIGINAL_RESUME_DENIALS

        def stable_output() -> None:
            stable_preview()
            if (
                type(output) is not OfflineScheduleResumeReview
                or any(a is not b for a, b in zip((
                    output.quarantine_chain_sha256, output.quarantined_count,
                    output.next_occurrence_id, output.next_state,
                    output.preview_sha256, output.review_sha256,
                ), pinned, strict=True))
                or any(vars(_RESULT_TYPE).get(key) is not descriptor
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
        denied_quarantine(last)
        stable()
        stable_preview()
        stable_output()
        if not same_witness(last, retained_quarantine):
            raise ScheduleResumeRejected("quarantine history changed after witness")
        return output
    except (ScheduleQuarantineRejected, SchedulePreviewRejected, sqlite3.Error) as exc:
        raise ScheduleResumeRejected("offline schedule resume verification rejected") from exc
