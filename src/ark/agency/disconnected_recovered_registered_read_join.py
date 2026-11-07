"""Deny-only reconciliation of recovered mock READs with registry-bound receipts.

This opt-in join requires one common fixture req_ identity across a synthetic
READ journal. Registered act_ identities remain distinct. All inputs are local
caller-supplied witnesses: separate SQLite reads cannot prove cross-store
atomicity, actual tool execution, historical consent, or independent custody.
No ToolBackend is invoked and no replay/WRITE permission can be produced.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

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
from .disconnected_read_journal import ReadJournalSnapshot, ReadJournalWitness
from .disconnected_read_recovery_journal_bridge import (
    ReadRecoveryJournalRejected,
    ReadRecoveryJournalReview,
    review_detached_read_journal_recovery,
)
from .disconnected_read_recovery_schedule import ReadRecoveryStep
from .disconnected_registered_batch_receipt_review import (
    RegisteredBatchReceiptRejected,
    RegisteredBatchReceiptReview,
    review_registered_batch_receipt,
)
from .disconnected_registered_batch_receipt_set import RegisteredBatchStepEvidence
from .policy import PermissionGate
from .registry import ToolRegistry

_DOMAIN = b"ARK-recovered-registered-read-join-v1\0"
_RECOVERY_DOMAIN = b"ARK-detached-read-journal-recovery-join-v1\0"
_CHILD_DOMAIN = b"ARK-disconnected-registered-batch-receipt-v1\0"
_DENIED = (
    "backend_dispatched",
    "write_authorized",
    "automatic_replay_authorized",
    "external_outcome_proven",
    "independent_custody_proven",
)


class RecoveredRegisteredReadRejected(ValueError):
    """Recovered READ history and registered mock receipt disagree."""


@dataclass(frozen=True, slots=True)
class RecoveredRegisteredReadReview:
    plan_digest: str
    schedule_digest: str
    recovery_digest: str
    journal_tip_sha256: str
    # Ordered: step ID, registered act_ ID, fixture req_ ID, child review SHA.
    registered_steps: tuple[tuple[str, str, str, str], ...]
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
    def external_outcome_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_REPORT = RecoveredRegisteredReadReview
_CHILD = RegisteredBatchReceiptReview
_RECOVERY = ReadRecoveryJournalReview
# Denied-only flags must preserve their import-time implementation, not an
# arbitrary preinstalled callback which happens to return False.
_ORIGINAL_REPORT_DENIALS = tuple(vars(_REPORT)[key] for key in _DENIED)
_REPORT_FIELDS = (
    "plan_digest", "schedule_digest", "recovery_digest",
    "journal_tip_sha256", "registered_steps", "join_sha256",
)
_REPORT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT)[key] for key in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT).get(key) for key in _REPORT_HOOKS)


def _require_original_result_carrier() -> None:
    """Reject patched constructors/slots before executing any report getter."""
    if (
        RecoveredRegisteredReadReview is not _REPORT
        or any(
            vars(_REPORT).get(name) is not original
            for names, originals in (
                (_DENIED, _ORIGINAL_REPORT_DENIALS),
                (_REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS),
                (_REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise RecoveredRegisteredReadRejected("recovery carrier changed during join")


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(
        domain + json.dumps(
            value, ensure_ascii=True, separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()


def review_recovered_registered_reads(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    steps: tuple[ReadRecoveryStep, ...],
    snapshot: ReadJournalSnapshot,
    retained_journal: ReadJournalWitness,
    evidence: tuple[RegisteredBatchStepEvidence, ...],
    registry: ToolRegistry,
    gate: PermissionGate,
    *,
    retained_plan_digest: str,
    observed_at_ms: int,
) -> RecoveredRegisteredReadReview:
    """Join exactly the successful prefix/subset; never retry pending READs.

    Every synthetic success must have one common-request SQLite receipt AND
    one currently valid registry-bound witness. Failed/uncertain/pending
    operations must have neither. The retained plan and journal tips must
    have been preserved separately by the caller; neither is authenticated.
    """
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(schedule) is not DisconnectedBatchSchedule
        or type(steps) is not tuple
        or type(plan.steps) is not tuple
        or not 1 <= len(plan.steps) == len(steps) <= 24
        or type(snapshot) is not ReadJournalSnapshot
        or type(retained_journal) is not ReadJournalWitness
        or type(evidence) is not tuple
        or any(type(row) is not ReadRecoveryStep for row in steps)
        or any(type(row) is not DisconnectedBatchStep for row in plan.steps)
        or any(type(item) is not RegisteredBatchStepEvidence for item in evidence)
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(retained_plan_digest) is not str
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms < (1 << 63)
    ):
        raise RecoveredRegisteredReadRejected("exact bounded recovery join required")
    _require_original_result_carrier()

    plan_fields = (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest)
    schedule_fields = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    plan_carriers = tuple(plan.steps)
    plan_rows = tuple(
        (row.step_id, row.operation, row.canonical_args_json, row.depends_on)
        for row in plan_carriers
    )
    step_carriers = tuple(steps)
    step_rows = tuple(
        (row.step_id, row.operation, row.depends_on, row.state, row.result_sha256)
        for row in steps
    )
    evidence_carriers = tuple(evidence)
    evidence_rows = tuple(
        (item.journal, item.retained_journal, item.link, item.call,
         item.grants, item.request, item.result, item.binding)
        for item in evidence
    )
    snapshot_fields = (snapshot.witness, snapshot.receipts)
    retained_fields = (retained_journal.count, retained_journal.tip_sha256)
    success = tuple(row.step_id for row in steps if row.state == "SUCCEEDED")
    if len(evidence) != len(success):
        raise RecoveredRegisteredReadRejected("successful READ witness count differs")

    def stable() -> None:
        _require_original_result_carrier()
        if (
            type(plan) is not DisconnectedBatchPlan
            or type(schedule) is not DisconnectedBatchSchedule
            or any(now is not old for now, old in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json,
                 plan.plan_digest), plan_fields, strict=True,
            ))
            or any(now is not old for now, old in zip(
                (schedule.request_id, schedule.plan_digest, schedule.waves,
                 schedule.schedule_digest), schedule_fields, strict=True,
            ))
            or type(plan.steps) is not tuple
            or len(plan.steps) != len(plan_carriers)
            or len(steps) != len(step_carriers)
            or len(evidence) != len(evidence_carriers)
            or any(
                row is not original or type(row) is not DisconnectedBatchStep
                or any(now is not old for now, old in zip(
                    (row.step_id, row.operation, row.canonical_args_json,
                     row.depends_on), fields, strict=True,
                ))
                for row, original, fields in zip(
                    plan.steps, plan_carriers, plan_rows, strict=True,
                )
            )
            or any(
                row is not original or type(row) is not ReadRecoveryStep
                or any(now is not old for now, old in zip(
                    (row.step_id, row.operation, row.depends_on, row.state,
                     row.result_sha256), fields, strict=True,
                ))
                for row, original, fields in zip(
                    steps, step_carriers, step_rows, strict=True,
                )
            )
            or any(
                item is not original or type(item) is not RegisteredBatchStepEvidence
                or any(now is not old for now, old in zip(
                    (item.journal, item.retained_journal, item.link, item.call,
                     item.grants, item.request, item.result, item.binding),
                    fields, strict=True,
                ))
                for item, original, fields in zip(
                    evidence, evidence_carriers, evidence_rows, strict=True,
                )
            )
            or type(snapshot) is not ReadJournalSnapshot
            or snapshot.witness is not snapshot_fields[0]
            or snapshot.receipts is not snapshot_fields[1]
            or type(retained_journal.count) is not int
            or type(retained_journal.tip_sha256) is not str
            or retained_journal.count != retained_fields[0]
            or retained_journal.tip_sha256 != retained_fields[1]
        ):
            raise RecoveredRegisteredReadRejected("recovery carrier changed during join")

    def inspect() -> tuple[object, ...]:
        stable()
        verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
        verify_disconnected_batch_schedule(
            schedule, plan, retained_digest=retained_plan_digest,
        )
        stable()
        if any(
            (a[0], a[1], a[3]) != (b[0], b[1], b[2])
            for a, b in zip(plan_rows, step_rows, strict=True)
        ):
            raise RecoveredRegisteredReadRejected("recovery does not match exact DAG")
        recovered = review_detached_read_journal_recovery(
            snapshot.receipts[0].request_id if snapshot.receipts
            else request_id_for_empty,
            steps, snapshot, retained_journal,
        )
        stable()
        if (
            type(recovered) is not _RECOVERY
            or type(recovered.successful_step_ids) is not tuple
            or recovered.successful_step_ids != success
            # One valid journal cannot be rebound to a different DAG run.
            or recovered.request_id != plan_fields[0]
            or recovered.journal_tip_sha256 != retained_fields[1]
            or recovered.review_sha256 != _digest(
                _RECOVERY_DOMAIN,
                (
                    recovered.request_id, recovered.schedule_digest,
                    recovered.journal_tip_sha256, recovered.successful_step_ids,
                ),
            )
            or any(getattr(recovered, key) is not False for key in (
                "backend_dispatched", "external_result_proven",
                "automatic_replay_authorized", "independent_custody_proven",
            ))
        ):
            raise RecoveredRegisteredReadRejected("recovery report or digest disagrees")
        stable()

        joined: list[tuple[str, str, str, str]] = []
        for step_id, item in zip(success, evidence, strict=True):
            stable()
            if (
                item.link.step_id != step_id
                or item.request.request_id != recovered.request_id
                or item.link.fixture_request_id != recovered.request_id
                or item.result.result_digest != next(
                    row[4] for row in step_rows if row[0] == step_id
                )
            ):
                raise RecoveredRegisteredReadRejected(
                    "registered fixture differs from recovered success"
                )
            child = review_registered_batch_receipt(
                plan, schedule, retained_plan_digest,
                item.journal, item.retained_journal, item.link,
                registry, gate, item.call, item.grants, step_id,
                item.request, item.result, item.binding,
                observed_at_ms=observed_at_ms,
            )
            stable()
            if type(child) is not _CHILD:
                raise RecoveredRegisteredReadRejected("registered child type changed")
            child_fields = (
                child.step_id, child.plan_digest, child.schedule_digest,
                child.wave_index, child.action_request_id,
                child.fixture_request_id, child.link_sha256,
                child.journal_count, child.journal_tip_sha256,
            )
            if (
                child.step_id != step_id
                or child.plan_digest != plan_fields[3]
                or child.schedule_digest != schedule_fields[3]
                or child.action_request_id != item.call.request_id
                or child.fixture_request_id != recovered.request_id
                or child.link_sha256 != item.link.link_sha256
                or child.journal_count != retained_fields[0]
                or child.journal_tip_sha256 != retained_fields[1]
                or child.review_sha256 != _digest(_CHILD_DOMAIN, child_fields)
                or any(getattr(child, key) is not False for key in (
                    "backend_dispatched", "write_authorized",
                    "automatic_replay_authorized",
                    "dependencies_completed_proven", "independent_custody_proven",
                ))
                or (
                    child.step_id, child.plan_digest, child.schedule_digest,
                    child.wave_index, child.action_request_id,
                    child.fixture_request_id, child.link_sha256,
                    child.journal_count, child.journal_tip_sha256,
                ) != child_fields
            ):
                raise RecoveredRegisteredReadRejected(
                    "registered child witness disagrees"
                )
            stable()
            # The child denial getters are callbacks. A callback returning
            # False may still rewrite the receipt hash *after* its first
            # digest comparison. Never commit that unverified value to the
            # parent recovery join.
            if (
                type(child) is not _CHILD
                or (
                    child.step_id, child.plan_digest, child.schedule_digest,
                    child.wave_index, child.action_request_id,
                    child.fixture_request_id, child.link_sha256,
                    child.journal_count, child.journal_tip_sha256,
                ) != child_fields
                or type(child.review_sha256) is not str
                or child.review_sha256 != _digest(_CHILD_DOMAIN, child_fields)
            ):
                raise RecoveredRegisteredReadRejected(
                    "registered child changed during denial callbacks"
                )
            joined.append((
                step_id, child.action_request_id,
                child.fixture_request_id, child.review_sha256,
            ))
        stable()
        return (
            plan_fields[3], schedule_fields[3],
            recovered.schedule_digest, recovered.journal_tip_sha256,
            tuple(joined),
        )

    # With no receipt, the shared request ID is not inferable from SQLite.
    # Use the explicit plan request ID only for an empty diagnostic history.
    request_id_for_empty = plan_fields[0]
    try:
        first = inspect()
        if inspect() != first:
            raise RecoveredRegisteredReadRejected("join drifted across reads")
        digest = _digest(_DOMAIN, first)
        stable()
        _require_original_result_carrier()
        review = _REPORT(*first, digest)
        _require_original_result_carrier()
        pinned = (*first, digest)
        descriptors = _ORIGINAL_REPORT_DENIALS

        def stable_result() -> None:
            _require_original_result_carrier()
            stable()
            if (
                type(review) is not _REPORT
                or any(now is not old for now, old in zip(
                    (review.plan_digest, review.schedule_digest,
                     review.recovery_digest, review.journal_tip_sha256,
                     review.registered_steps, review.join_sha256),
                    pinned, strict=True,
                ))
                or any(
                    vars(_REPORT).get(key) is not original
                    for key, original in zip(_DENIED, descriptors, strict=True)
                )
            ):
                raise RecoveredRegisteredReadRejected("recovery join result changed")

        stable_result()
        for name in _DENIED:
            if getattr(review, name) is not False:
                raise RecoveredRegisteredReadRejected("join acquired authority")
            stable_result()
        if inspect() != first:
            raise RecoveredRegisteredReadRejected("join drifted after denial")
        stable_result()
        return review
    except RecoveredRegisteredReadRejected:
        raise
    except (
        DisconnectedBatchRejected, ReadRecoveryJournalRejected,
        RegisteredBatchReceiptRejected, TypeError, AttributeError, KeyError,
    ) as exc:
        raise RecoveredRegisteredReadRejected(
            "recovered registered READ review denied"
        ) from exc
