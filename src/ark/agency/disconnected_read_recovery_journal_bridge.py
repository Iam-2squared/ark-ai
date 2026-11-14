"""Read-only reconciliation of detached READ recovery with a retained SQLite tip.

This is a diagnostic bridge between two local, separately supplied witnesses.
It never dispatches, replays or authenticates a tool call, real-world result,
clock, permission, actor, or durable cross-store atomicity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    _check_receipt,
    _require_original_read_carriers,
    _require_original_snapshot_class,
    genesis_witness,
)
from .disconnected_read_recovery_schedule import (
    DetachedReadRecoverySchedule,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_DOMAIN = b"ARK-detached-read-journal-recovery-join-v1\0"
_DENIALS = (
    "backend_dispatched",
    "external_result_proven",
    "automatic_replay_authorized",
    "independent_custody_proven",
)


class ReadRecoveryJournalRejected(ValueError):
    """The offline READ history disagrees with its retained journal tip."""


@dataclass(frozen=True, slots=True)
class ReadRecoveryJournalReview:
    request_id: str
    schedule_digest: str
    journal_tip_sha256: str
    successful_step_ids: tuple[str, ...]
    review_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def external_result_proven(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_REPORT = ReadRecoveryJournalReview

# Import-time custody is required: a preinstalled False-only descriptor is
# still an arbitrary callback, not the denial definition shipped by ARK.
_SNAPSHOT_DENIALS = (
    "dispatch_authorized", "effect_proven",
    "automatic_replay_authorized", "independent_custody_proven",
)
_WITNESS_DENIALS = (
    "dispatch_authorized", "effect_proven",
    "replay_authorized", "independent_custody_proven",
)
_ORIGINAL_SNAPSHOT_DENIALS = tuple(
    getattr(ReadJournalSnapshot, name) for name in _SNAPSHOT_DENIALS
)
_ORIGINAL_WITNESS_DENIALS = tuple(
    getattr(ReadJournalWitness, name) for name in _WITNESS_DENIALS
)
_ORIGINAL_REPORT_DENIALS = tuple(
    getattr(_REPORT, name) for name in _DENIALS
)
# The frozen, slotted report is not an immutable *class*. Verify the original
# constructor, field slots and lookup machinery before executing user-reachable
# callbacks or reading retained recovery carriers. False-valued properties
# alone cannot certify that construction is inert.
_REPORT_FIELDS = (
    "request_id", "schedule_digest", "journal_tip_sha256",
    "successful_step_ids", "review_sha256",
)
_REPORT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT)[name] for name in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(
    vars(_REPORT).get(name) for name in _REPORT_HOOKS
)


def _require_original_report() -> None:
    if (
        ReadRecoveryJournalReview is not _REPORT
        or any(
            vars(_REPORT).get(name) is not original
            for names, originals in (
                (_REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS),
                (_REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS),
                (_DENIALS, _ORIGINAL_REPORT_DENIALS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ReadRecoveryJournalRejected(
            "READ recovery report carrier changed: constructor or authority definition changed"
        )


# Imported source guards check raw class dictionaries, never a potentially
# hostile snapshot/receipt descriptor. Bind them before the first field read.
_ORIGINAL_SOURCE_CHECKS = (
    _require_original_read_carriers,
    _require_original_snapshot_class,
)


def _require_original_source_carriers() -> None:
    if (
        _require_original_read_carriers is not _ORIGINAL_SOURCE_CHECKS[0]
        or _require_original_snapshot_class is not _ORIGINAL_SOURCE_CHECKS[1]
    ):
        raise ReadRecoveryJournalRejected("READ source validator changed")
    try:
        _require_original_read_carriers()
        _require_original_snapshot_class()
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReadRecoveryJournalRejected("READ source descriptor changed") from exc


def review_detached_read_journal_recovery(
    request_id: str,
    steps: tuple[ReadRecoveryStep, ...],
    snapshot: ReadJournalSnapshot,
    retained: ReadJournalWitness,
) -> ReadRecoveryJournalReview:
    """Match ALL claimed synthetic successes to the retained SQLite receipt chain.

    In particular, a merely valid journal tip is insufficient: each successful
    step must have exactly one matching receipt, with ancestors appended first,
    and failed/unstarted/uncertain steps must have none. The retained tip must
    have been preserved independently of the SQLite database by the caller.
    """
    _require_original_report()
    _require_original_source_carriers()
    if (
        type(request_id) is not str
        or type(steps) is not tuple
        or type(snapshot) is not ReadJournalSnapshot
        or type(retained) is not ReadJournalWitness
        or type(snapshot.witness) is not ReadJournalWitness
        or type(snapshot.receipts) is not tuple
        or not 1 <= len(steps) <= 24
        or len(snapshot.receipts) > 128
        or any(type(step) is not ReadRecoveryStep for step in steps)
        or any(type(row) is not ReadReceipt for row in snapshot.receipts)
    ):
        raise ReadRecoveryJournalRejected("exact bounded recovery evidence required")

    # Capture the original deny-only descriptors BEFORE invoking the mutable
    # schedule callback. A replacement getter returning False is still a
    # different authority surface and must not be silently accepted.
    snapshot_denials = _SNAPSHOT_DENIALS
    witness_denials = _WITNESS_DENIALS
    snapshot_descriptors = _ORIGINAL_SNAPSHOT_DENIALS
    witness_descriptors = _ORIGINAL_WITNESS_DENIALS
    report_descriptors = _ORIGINAL_REPORT_DENIALS
    original_steps = tuple(steps)
    step_fields = tuple(
        (row.step_id, row.operation, row.depends_on, row.state, row.result_sha256)
        for row in original_steps
    )
    rows = snapshot.receipts
    row_fields = tuple(
        (row.request_id, row.step_id, row.operation,
         row.input_digest, row.result_digest)
        for row in rows
    )
    witness = snapshot.witness
    witness_fields = (witness.count, witness.tip_sha256)
    retained_fields = (retained.count, retained.tip_sha256)
    original_request = request_id

    def stable() -> None:
        _require_original_report()
        _require_original_source_carriers()
        if (
            request_id is not original_request
            or type(steps) is not tuple
            or len(steps) != len(original_steps)
            or type(snapshot) is not ReadJournalSnapshot
            or snapshot.witness is not witness
            or snapshot.receipts is not rows
            or type(snapshot.receipts) is not tuple
            or len(rows) != len(row_fields)
            or type(witness) is not ReadJournalWitness
            or type(retained) is not ReadJournalWitness
            or any(
                getattr(ReadJournalSnapshot, key) is not original
                for key, original in zip(
                    snapshot_denials, snapshot_descriptors, strict=True,
                )
            )
            or any(
                getattr(ReadJournalWitness, key) is not original
                for key, original in zip(
                    witness_denials, witness_descriptors, strict=True,
                )
            )
            or any(
                getattr(_REPORT, key) is not original
                for key, original in zip(
                    _DENIALS, report_descriptors, strict=True,
                )
            )
            or type(witness.count) is not int
            or type(retained.count) is not int
            or type(witness.tip_sha256) is not str
            or type(retained.tip_sha256) is not str
            or witness.count != witness_fields[0]
            or witness.tip_sha256 != witness_fields[1]
            or retained.count != retained_fields[0]
            or retained.tip_sha256 != retained_fields[1]
            or any(
                row is not original or type(row) is not ReadRecoveryStep
                or any(now is not first for now, first in zip(
                    (row.step_id, row.operation, row.depends_on,
                     row.state, row.result_sha256), fields, strict=True,
                ))
                for row, original, fields in zip(
                    steps, original_steps, step_fields, strict=True,
                )
            )
            or any(
                row is not original or type(row) is not ReadReceipt
                or any(now is not first for now, first in zip(
                    (row.request_id, row.step_id, row.operation,
                     row.input_digest, row.result_digest), fields, strict=True,
                ))
                for row, original, fields in zip(
                    rows, rows, row_fields, strict=True,
                )
            )
        ):
            raise ReadRecoveryJournalRejected("READ recovery evidence carrier changed")

    stable()
    try:
        schedule = schedule_detached_read_recovery(request_id, steps)
        stable()
        if (
            type(schedule) is not DetachedReadRecoverySchedule
            or schedule.request_id != request_id
            or len(schedule.decisions) != len(steps)
        ):
            raise ReadRecoveryJournalRejected("recovery schedule mismatched")
        prior = genesis_witness()
        if (
            type(witness_fields[0]) is not int
            or type(retained_fields[0]) is not int
            or witness_fields != retained_fields
            or witness_fields[0] != len(rows)
            or len(rows) > 128
        ):
            raise ReadRecoveryJournalRejected("retained READ journal tip disagrees")
        tip = prior.tip_sha256
        row_by_step: dict[str, tuple[int, ReadReceipt]] = {}
        for index, row in enumerate(rows, 1):
            stable()
            _check_receipt(row)
            if (
                row.request_id != request_id
                or row.step_id in row_by_step
            ):
                raise ReadRecoveryJournalRejected("foreign or duplicate READ receipt")
            tip = _chain(tip, index, row)
            row_by_step[row.step_id] = (index, row)
        if tip != witness_fields[1]:
            raise ReadRecoveryJournalRejected("READ journal chain disagrees")
        success: list[str] = []
        for step_id, operation, dependencies, state, result_sha in step_fields:
            stable()
            present = row_by_step.get(step_id)
            if state == "SUCCEEDED":
                if (
                    present is None
                    or present[1].operation != operation
                    or present[1].result_digest != result_sha
                    or any(
                        dependency not in row_by_step
                        or row_by_step[dependency][0] >= present[0]
                        for dependency in dependencies
                    )
                ):
                    raise ReadRecoveryJournalRejected("successful READ receipt mismatched")
                success.append(step_id)
            elif present is not None:
                raise ReadRecoveryJournalRejected("unresolved READ has a receipt")
        if len(success) != len(rows):
            raise ReadRecoveryJournalRejected("unexpected READ journal evidence")
        stable()
        payload = (
            request_id, schedule.schedule_digest, tip, tuple(success),
        )
        digest = hashlib.sha256(
            _DOMAIN + json.dumps(
                payload, separators=(",", ":"), ensure_ascii=True,
            ).encode("ascii")
        ).hexdigest()
        _require_original_report()
        review = _REPORT(*payload, digest)
        _require_original_report()
        fields = (
            review.request_id, review.schedule_digest,
            review.journal_tip_sha256, review.successful_step_ids,
            review.review_sha256,
        )
        descriptors = report_descriptors

        def stable_review() -> None:
            _require_original_report()
            if (
                type(review) is not _REPORT
                or any(now is not first for now, first in zip(
                    (
                        review.request_id, review.schedule_digest,
                        review.journal_tip_sha256, review.successful_step_ids,
                        review.review_sha256,
                    ), fields, strict=True,
                ))
                or any(
                    getattr(_REPORT, key) is not descriptor
                    for key, descriptor in zip(
                        _DENIALS, descriptors, strict=True,
                    )
                )
            ):
                raise ReadRecoveryJournalRejected("READ recovery review changed")
            stable()

        stable_review()
        if any(
            getattr(snapshot, name) is not False
            for name in (
                "dispatch_authorized", "effect_proven",
                "automatic_replay_authorized", "independent_custody_proven",
            )
        ):
            raise ReadRecoveryJournalRejected("snapshot claims execution authority")
        stable_review()
        if any(
            getattr(witness, name) is not False
            or getattr(retained, name) is not False
            for name in (
                "dispatch_authorized", "effect_proven",
                "replay_authorized", "independent_custody_proven",
            )
        ):
            raise ReadRecoveryJournalRejected("witness claims execution authority")
        stable_review()
        for key in _DENIALS:
            if getattr(review, key) is not False:
                raise ReadRecoveryJournalRejected("review claims execution authority")
            stable_review()
        # A final denied-authority property is a callback boundary.
        if schedule_detached_read_recovery(request_id, steps).schedule_digest != payload[1]:
            raise ReadRecoveryJournalRejected("READ schedule changed on final review")
        stable_review()
        return review
    except ReadRecoveryJournalRejected:
        raise
    except (TypeError, ValueError, AttributeError, KeyError) as exc:
        raise ReadRecoveryJournalRejected("READ recovery evidence rejected") from exc
