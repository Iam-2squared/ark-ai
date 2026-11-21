"""Read-only partial-success join across a detached failure archive and registered READs.

A caller-held failure mask drives the terminal simulation, never a journal.
Only synthetic SUCCEEDED steps may supply registered READ evidence. Separate
archive/SQLite observations are not atomic and prove no actual execution,
absence of other receipts, trusted clock, consent or replay permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .disconnected_batch_failure_archive import (
    ArchivedDisconnectedFailure,
    DisconnectedFailureArchiveRejected,
    review_disconnected_failure_archive,
)
from .disconnected_batch_failure_fixture import (
    DisconnectedFailureFixtureReceipt,
    DisconnectedFailureFixtureRejected,
    simulate_disconnected_failure_fixture,
)
from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    DisconnectedBatchRejected,
    DisconnectedBatchStep,
    verify_disconnected_batch_plan,
)
from .disconnected_batch_schedule import (
    DisconnectedBatchSchedule,
    verify_disconnected_batch_schedule,
)
from .disconnected_registered_batch_receipt_review import (
    RegisteredBatchReceiptRejected,
    RegisteredBatchReceiptReview,
    review_registered_batch_receipt,
)
from .disconnected_registered_batch_receipt_set import RegisteredBatchStepEvidence
from .policy import PermissionGate
from .registry import ToolRegistry

_DOMAIN = b"ARK-detached-partial-registered-failure-join-v1\0"
_CHILD_DOMAIN = b"ARK-disconnected-registered-batch-receipt-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DENIALS = (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "failure_authenticated", "dependencies_completed_proven",
    "cross_store_atomicity_proven",
)


class PartialFailureJoinRejected(ValueError):
    """A partial hypothetical DAG and independently retained READs disagree."""


@dataclass(frozen=True, slots=True)
class PartialFailureJoinReview:
    plan_digest: str
    schedule_digest: str
    failure_file_sha256: str
    failure_fixture_digest: str
    terminal_states: tuple[tuple[str, str], ...]
    # (step_id, registered receipt sha, journal tip sha) only for SUCCEEDED.
    successful_read_receipts: tuple[tuple[str, str, str], ...]
    join_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def failure_authenticated(self) -> bool:
        return False

    @property
    def dependencies_completed_proven(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False


_CHILD_DENIALS = (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "dependencies_completed_proven", "independent_custody_proven",
)
_ARCHIVE_DENIALS = (
    "external_dispatch_authorized", "write_authorized",
    "automatic_replay_authorized", "failure_authenticated", "real_outcome_proven",
)
_RECEIPT_DENIALS = (
    "dispatch_authorized", "write_authorized", "automatic_replay_authorized",
    "failure_authenticated", "external_outcome_verified",
)
_ORIGINALS = tuple(
    (cls, names, tuple(getattr(cls, name) for name in names))
    for cls, names in (
        (PartialFailureJoinReview, _DENIALS),
        (RegisteredBatchReceiptReview, _CHILD_DENIALS),
        (ArchivedDisconnectedFailure, _ARCHIVE_DENIALS),
        (DisconnectedFailureFixtureReceipt, _RECEIPT_DENIALS),
    )
)


def _authority_intact() -> None:
    for cls, names, originals in _ORIGINALS:
        if any(getattr(cls, name) is not original for name, original in zip(
            names, originals, strict=True,
        )):
            raise PartialFailureJoinRejected("partial join authority definition changed")


def _hash(fields: object, domain: bytes) -> str:
    raw = json.dumps(
        fields, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(domain + raw).hexdigest()


def review_partial_registered_failure_archive(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    evidence: tuple[tuple[str, RegisteredBatchStepEvidence], ...],
    registry: ToolRegistry,
    gate: PermissionGate,
    *,
    retained_plan_digest: str,
    retained_failed_step_ids: tuple[str, ...],
    path: Path,
    retained_file_sha256: str,
    observed_at_ms: int,
) -> PartialFailureJoinReview:
    """Reconcile SUCCESS receipts only, excluding FAILED/BLOCKED claims.

    The failure set and archive digest are independently caller-retained pins.
    A blocked step with a receipt is NOT proof of historical execution or a
    valid basis for retry; this review never searches for missing receipts.
    """
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(schedule) is not DisconnectedBatchSchedule
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(evidence) is not tuple
        or type(retained_failed_step_ids) is not tuple
        or type(retained_plan_digest) is not str
        or _SHA.fullmatch(retained_plan_digest) is None
        or type(retained_file_sha256) is not str
        or _SHA.fullmatch(retained_file_sha256) is None
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms < (1 << 63)
        or type(plan.steps) is not tuple
        or not 1 <= len(plan.steps) <= 24
        or len(evidence) > len(plan.steps)
        or any(
            type(entry) is not tuple or len(entry) != 2
            or type(entry[0]) is not str
            or type(entry[1]) is not RegisteredBatchStepEvidence
            for entry in evidence
        )
    ):
        raise PartialFailureJoinRejected("exact bounded partial READ join required")
    _authority_intact()
    plan_epoch = (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest)
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    steps = tuple(
        (step, step.step_id, step.operation, step.canonical_args_json, step.depends_on)
        for step in plan.steps
    )
    pins = tuple((
        entry, entry[0], entry[1],
        entry[1].journal, entry[1].retained_journal, entry[1].link,
        entry[1].call, entry[1].grants, entry[1].request,
        entry[1].result, entry[1].binding,
    ) for entry in evidence)

    def stable() -> None:
        _authority_intact()
        if (
            type(plan) is not DisconnectedBatchPlan
            or type(schedule) is not DisconnectedBatchSchedule
            or any(a is not b for a, b in zip((
                plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest,
            ), plan_epoch, strict=True))
            or any(a is not b for a, b in zip((
                schedule.request_id, schedule.plan_digest, schedule.waves,
                schedule.schedule_digest,
            ), schedule_epoch, strict=True))
            or type(plan.steps) is not tuple
            or len(plan.steps) != len(steps)
            or any(
                type(step) is not DisconnectedBatchStep
                or step is not original
                or any(a is not b for a, b in zip((
                    step.step_id, step.operation, step.canonical_args_json,
                    step.depends_on,
                ), (sid, operation, args, deps), strict=True))
                for step, (original, sid, operation, args, deps)
                in zip(plan.steps, steps, strict=True)
            )
            or len(evidence) != len(pins)
            or any(
                entry is not old_entry or entry[0] is not sid
                or entry[1] is not item
                or any(now is not original for now, original in zip((
                    item.journal, item.retained_journal, item.link, item.call,
                    item.grants, item.request, item.result, item.binding,
                ), fields, strict=True))
                for entry, (old_entry, sid, item, *fields)
                in zip(evidence, pins, strict=True)
            )
        ):
            raise PartialFailureJoinRejected("partial join input carriers changed")

    def review_once() -> tuple[object, ...]:
        stable()
        verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
        verify_disconnected_batch_schedule(
            schedule, plan, retained_digest=retained_plan_digest,
        )
        stable()
        archive = review_disconnected_failure_archive(
            plan, schedule, retained_plan_digest=retained_plan_digest,
            retained_failed_step_ids=retained_failed_step_ids,
            path=path, retained_file_sha256=retained_file_sha256,
        )
        stable()
        fixture = simulate_disconnected_failure_fixture(
            plan, schedule, retained_digest=retained_plan_digest,
            failed_step_ids=retained_failed_step_ids,
        )
        stable()
        terminal = fixture.terminal_states
        successes = tuple(step for step, state in terminal if state == "SUCCEEDED")
        if (
            type(archive) is not ArchivedDisconnectedFailure
            or type(fixture) is not DisconnectedFailureFixtureReceipt
            or archive.file_sha256 != retained_file_sha256
            or archive.fixture_digest != fixture.fixture_digest
            or archive.projection_digest != fixture.projection_digest
            or archive.failed_step_ids != retained_failed_step_ids
            or archive.terminal_counts != tuple(
                sum(state == target for _, state in terminal)
                for target in ("SUCCEEDED", "FAILED", "BLOCKED")
            )
            or tuple(entry[0] for entry in evidence) != successes
        ):
            raise PartialFailureJoinRejected("failure mask or successful subset disagrees")
        # Archive/fixture receipts are caller-held objects with overridable
        # safety getters. Retain their exact carriers BEFORE registered READ
        # callbacks and denial checks so a reentrant False-only getter cannot
        # revise the terminal mask or file identity after initial validation.
        archive_epoch = (
            archive.file_sha256, archive.fixture_digest,
            archive.projection_digest, archive.failed_step_ids,
            archive.terminal_counts,
        )
        fixture_epoch = (
            fixture.fixture_digest, fixture.projection_digest,
            fixture.terminal_states, fixture.result_digests,
        )

        def stable_failure_reports() -> None:
            if (
                type(archive) is not ArchivedDisconnectedFailure
                or type(fixture) is not DisconnectedFailureFixtureReceipt
                or any(now is not old for now, old in zip((
                    archive.file_sha256, archive.fixture_digest,
                    archive.projection_digest, archive.failed_step_ids,
                    archive.terminal_counts,
                ), archive_epoch, strict=True))
                or any(now is not old for now, old in zip((
                    fixture.fixture_digest, fixture.projection_digest,
                    fixture.terminal_states, fixture.result_digests,
                ), fixture_epoch, strict=True))
            ):
                raise PartialFailureJoinRejected(
                    "failure archive or fixture changed during receipt review"
                )

        expected_binding = dict(fixture.result_digests)
        rows: list[tuple[str, str, str]] = []
        for (step_id, item) in evidence:
            stable()
            # The detached failure simulator binds synthetic successful READs
            # to the PLAN request ID. A different request ID is not the same
            # fixture, even if the operation and result happen to be equal.
            if (
                item.request.request_id != plan.request_id
                or item.binding.request_bound_digest != expected_binding[step_id]
            ):
                raise PartialFailureJoinRejected("successful fixture request binding differs")
            child = review_registered_batch_receipt(
                plan, schedule, retained_plan_digest,
                item.journal, item.retained_journal, item.link,
                registry, gate, item.call, item.grants, step_id,
                item.request, item.result, item.binding,
                observed_at_ms=observed_at_ms,
            )
            stable()
            stable_failure_reports()
            fields = (
                child.step_id, child.plan_digest, child.schedule_digest,
                child.wave_index, child.action_request_id,
                child.fixture_request_id, child.link_sha256,
                child.journal_count, child.journal_tip_sha256,
                child.review_sha256,
            )
            if (
                type(child) is not RegisteredBatchReceiptReview
                or type(child.step_id) is not str
                or child.step_id != step_id
                or type(child.plan_digest) is not str
                or child.plan_digest != plan.plan_digest
                or type(child.schedule_digest) is not str
                or child.schedule_digest != schedule.schedule_digest
                or type(child.wave_index) is not int
                or tuple(index for index, wave in enumerate(schedule.waves)
                         if step_id in wave) != (child.wave_index,)
                or child.action_request_id != item.call.request_id
                or child.fixture_request_id != plan.request_id
                or child.link_sha256 != item.link.link_sha256
                or type(child.journal_count) is not int
                or child.journal_count != item.retained_journal.count
                or child.journal_tip_sha256 != item.retained_journal.tip_sha256
                or type(child.review_sha256) is not str
                or _SHA.fullmatch(child.review_sha256) is None
                or child.review_sha256 != _hash(fields[:-1], _CHILD_DOMAIN)
            ):
                raise PartialFailureJoinRejected("registered success receipt mismatch")
            for flag in _CHILD_DENIALS:
                if getattr(child, flag) is not False:
                    raise PartialFailureJoinRejected("child receipt granted authority")
                if tuple(getattr(child, name) for name in (
                    "step_id", "plan_digest", "schedule_digest", "wave_index",
                    "action_request_id", "fixture_request_id", "link_sha256",
                    "journal_count", "journal_tip_sha256", "review_sha256",
                )) != fields:
                    raise PartialFailureJoinRejected("child receipt mutated on denial")
                stable()
            rows.append((step_id, child.review_sha256, child.journal_tip_sha256))
        for item, names in (
            (archive, _ARCHIVE_DENIALS),
            (fixture, _RECEIPT_DENIALS),
        ):
            for name in names:
                if getattr(item, name) is not False:
                    raise PartialFailureJoinRejected("synthetic failure granted authority")
                stable()
                stable_failure_reports()
        stable()
        stable_failure_reports()
        return (
            archive.file_sha256, fixture.fixture_digest, terminal, tuple(rows),
        )

    try:
        first = review_once()
        if review_once() != first:
            raise PartialFailureJoinRejected("partial READ observations changed")
        fields = (
            plan.plan_digest, schedule.schedule_digest, *first,
        )
        report = PartialFailureJoinReview(*fields, _hash(fields, _DOMAIN))
        epoch = (*fields, report.join_sha256)

        def stable_report() -> None:
            if (
                type(report) is not PartialFailureJoinReview
                or any(a is not b for a, b in zip((
                    report.plan_digest, report.schedule_digest,
                    report.failure_file_sha256, report.failure_fixture_digest,
                    report.terminal_states, report.successful_read_receipts,
                    report.join_sha256,
                ), epoch, strict=True))
            ):
                raise PartialFailureJoinRejected("partial READ report changed")
            stable()

        stable_report()
        for name in _DENIALS:
            if getattr(report, name) is not False:
                raise PartialFailureJoinRejected("partial READ report gained authority")
            stable_report()
        if review_once() != first:
            raise PartialFailureJoinRejected("partial READ observations changed after denial")
        stable_report()
        return report
    except (
        DisconnectedBatchRejected, DisconnectedFailureArchiveRejected,
        DisconnectedFailureFixtureRejected, RegisteredBatchReceiptRejected,
        TypeError, AttributeError, KeyError,
    ) as exc:
        raise PartialFailureJoinRejected(
            "partial registered failure archive reconciliation denied"
        ) from exc
