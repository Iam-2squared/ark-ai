"""Bounded detached review of a whole registered READ batch.

Each step is re-read from its SQLite journal. These reads are separate:
neither their digests nor the aggregate proves cross-store atomicity,
completed dependencies, historical identity, consent or action authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .contracts import CapabilityGrant, ToolCall
from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    DisconnectedBatchRejected,
    verify_disconnected_batch_plan,
)
from .disconnected_batch_schedule import (
    DisconnectedBatchSchedule,
    verify_disconnected_batch_schedule,
)
from .disconnected_fixture_binding import DisconnectedFixtureBinding
from .disconnected_read_journal import DisconnectedReadJournal, ReadJournalWitness
from .disconnected_registered_batch_receipt_review import (
    RegisteredBatchReceiptRejected,
    RegisteredBatchReceiptReview,
    review_registered_batch_receipt,
)
from .disconnected_registered_fixture_join import RegisteredFixtureLink
from .disconnected_toolbox import DisconnectedToolRequest, DisconnectedToolResult
from .policy import PermissionGate
from .registry import ToolRegistry

_DOMAIN = b"ARK-registered-batch-receipt-set-v1\0"
_DENIALS = (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "dependencies_completed_proven", "independent_custody_proven",
)


class RegisteredBatchSetRejected(ValueError):
    """Not all detached READ receipts reconcile to the exact batch."""


@dataclass(frozen=True, slots=True)
class RegisteredBatchStepEvidence:
    journal: DisconnectedReadJournal
    retained_journal: ReadJournalWitness
    link: RegisteredFixtureLink
    call: ToolCall
    grants: tuple[CapabilityGrant, ...]
    request: DisconnectedToolRequest
    result: DisconnectedToolResult
    binding: DisconnectedFixtureBinding


@dataclass(frozen=True, slots=True)
class RegisteredBatchSetReview:
    plan_digest: str
    schedule_digest: str
    # step_id, act_ ID, req_ ID, wave index, independent step review hash
    step_receipts: tuple[tuple[str, str, str, int, str], ...]
    review_sha256: str

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
    def dependencies_completed_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_RESULT = RegisteredBatchSetReview
_EVIDENCE = RegisteredBatchStepEvidence


def review_registered_batch_receipt_set(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    retained_plan_digest: str,
    evidence: tuple[RegisteredBatchStepEvidence, ...],
    registry: ToolRegistry,
    gate: PermissionGate,
    *,
    observed_at_ms: int,
) -> RegisteredBatchSetReview:
    """Require one exact, ordered, registered READ witness for EVERY DAG step.

    Each evidence item is diagnostic only; no ToolBackend is invoked, no
    WRITE or retry permission is minted and no dependency is marked done.
    """
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(schedule) is not DisconnectedBatchSchedule
        or type(evidence) is not tuple
        or type(plan.steps) is not tuple
        or not 1 <= len(evidence) == len(plan.steps) <= 24
        or any(type(item) is not _EVIDENCE for item in evidence)
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms < (1 << 63)
    ):
        raise RegisteredBatchSetRejected("exact bounded batch evidence required")

    plan_epoch = (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest)
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest,
        schedule.waves, schedule.schedule_digest,
    )
    steps_epoch = tuple(
        (item, item.step_id, item.operation, item.canonical_args_json, item.depends_on)
        for item in plan.steps
    )
    evidence_epoch = tuple(
        (item, item.journal, item.retained_journal, item.link, item.call,
         item.grants, item.request, item.result, item.binding)
        for item in evidence
    )

    def stable_carriers() -> None:
        if (
            type(plan) is not DisconnectedBatchPlan
            or type(schedule) is not DisconnectedBatchSchedule
            or type(plan.steps) is not tuple
            or any(now is not prior for now, prior in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest),
                plan_epoch, strict=True,
            ))
            or any(now is not prior for now, prior in zip(
                (schedule.request_id, schedule.plan_digest,
                 schedule.waves, schedule.schedule_digest),
                schedule_epoch, strict=True,
            ))
            or len(plan.steps) != len(steps_epoch)
            or len(evidence) != len(evidence_epoch)
        ):
            raise RegisteredBatchSetRejected("batch carrier changed during review")
        for item, (old, *fields) in zip(evidence, evidence_epoch, strict=True):
            if (
                type(item) is not _EVIDENCE
                or item is not old
                or any(now is not prior for now, prior in zip((
                    item.journal, item.retained_journal, item.link, item.call,
                    item.grants, item.request, item.result, item.binding,
                ), fields, strict=True))
            ):
                raise RegisteredBatchSetRejected("step evidence changed during review")
        for step, (old, *fields) in zip(plan.steps, steps_epoch, strict=True):
            if (
                step is not old
                or any(now is not prior for now, prior in zip((
                    step.step_id, step.operation, step.canonical_args_json,
                    step.depends_on,
                ), fields, strict=True))
            ):
                raise RegisteredBatchSetRejected("DAG step changed during review")

    def verify_batch() -> None:
        stable_carriers()
        verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
        verify_disconnected_batch_schedule(
            schedule, plan, retained_digest=retained_plan_digest,
        )
        stable_carriers()

    def review_all() -> tuple[tuple[str, str, str, int, str], ...]:
        verify_batch()
        rows: list[tuple[str, str, str, int, str]] = []
        for step, item in zip(plan.steps, evidence, strict=True):
            stable_carriers()
            review = review_registered_batch_receipt(
                plan, schedule, retained_plan_digest,
                item.journal, item.retained_journal, item.link,
                registry, gate, item.call, item.grants, step.step_id,
                item.request, item.result, item.binding,
                observed_at_ms=observed_at_ms,
            )
            if type(review) is not RegisteredBatchReceiptReview:
                raise RegisteredBatchSetRejected("exact READ step receipt required")
            child_fields = (
                "step_id", "plan_digest", "schedule_digest", "wave_index",
                "action_request_id", "fixture_request_id", "link_sha256",
                "journal_count", "journal_tip_sha256", "review_sha256",
            )
            child_epoch = tuple(getattr(review, field) for field in child_fields)
            matching_waves = tuple(
                index for index, wave in enumerate(schedule.waves)
                if step.step_id in wave
            )
            if (
                len(matching_waves) != 1
                or review.step_id != step.step_id
                or review.plan_digest != plan.plan_digest
                or review.schedule_digest != schedule.schedule_digest
                or type(review.wave_index) is not int
                or review.wave_index != matching_waves[0]
                or review.action_request_id != item.call.request_id
                or review.fixture_request_id != item.request.request_id
                or review.link_sha256 != item.link.link_sha256
                or type(review.journal_count) is not int
                or review.journal_count != item.retained_journal.count
                or review.journal_tip_sha256 != item.retained_journal.tip_sha256
                or any(type(getattr(review, name)) is not str for name in (
                    "step_id", "plan_digest", "schedule_digest",
                    "action_request_id", "fixture_request_id", "link_sha256",
                    "journal_tip_sha256", "review_sha256",
                ))
                or len(review.review_sha256) != 64
                or any(char not in "0123456789abcdef" for char in review.review_sha256)
            ):
                raise RegisteredBatchSetRejected("READ step receipt disagrees with DAG")
            # Independently re-bind the child's canonical tuple to its domain-
            # separated digest. A well-formed 64-hex string alone is NOT a
            # valid receipt, even if an untrusted child reviewer returns it.
            expected_child_digest = hashlib.sha256(
                b"ARK-disconnected-registered-batch-receipt-v1\0"
                + json.dumps(
                    child_epoch[:-1], ensure_ascii=True, separators=(",", ":"),
                ).encode("ascii")
            ).hexdigest()
            if review.review_sha256 != expected_child_digest:
                raise RegisteredBatchSetRejected(
                    "READ step receipt digest disagrees with fields"
                )
            # Do not inherit a child's alleged authority or a field mutation
            # triggered by a false-valued final denial callback.
            if any(getattr(review, name) is not False for name in _DENIALS):
                raise RegisteredBatchSetRejected("READ step receipt gained authority")
            if tuple(getattr(review, field) for field in child_fields) != child_epoch:
                raise RegisteredBatchSetRejected("READ step receipt changed after denial")
            stable_carriers()
            rows.append((
                review.step_id, review.action_request_id,
                review.fixture_request_id, review.wave_index, review.review_sha256,
            ))
            stable_carriers()
        verify_batch()
        return tuple(rows)

    try:
        initial = review_all()
        if review_all() != initial:
            raise RegisteredBatchSetRejected("batch receipts changed across review passes")
        payload = (
            plan_epoch[3], schedule_epoch[3], initial,
        )
        digest = hashlib.sha256(
            _DOMAIN + json.dumps(
                payload, ensure_ascii=True, separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        result = _RESULT(*payload, digest)
        expected = (*payload, digest)
        # A final child/journal callback must not replace the authority
        # descriptors after the original denial pass has completed.
        denial_descriptors = tuple(getattr(_RESULT, name) for name in _DENIALS)

        def stable_result() -> None:
            if (
                type(result) is not _RESULT
                or any(now is not prior for now, prior in zip((
                    result.plan_digest, result.schedule_digest,
                    result.step_receipts, result.review_sha256,
                ), expected, strict=True))
                or any(
                    getattr(_RESULT, name) is not original
                    for name, original in zip(
                        _DENIALS, denial_descriptors, strict=True,
                    )
                )
            ):
                raise RegisteredBatchSetRejected("batch result changed after review")

        stable_result()
        for name in _DENIALS:
            if getattr(result, name) is not False:
                raise RegisteredBatchSetRejected("batch result gained authority")
            stable_result()
            stable_carriers()
        # The final pass closes mutations from false-valued denial getters;
        # it cannot make multiple SQLite stores a single atomic transaction.
        if review_all() != initial:
            raise RegisteredBatchSetRejected("batch receipts changed after denial")
        stable_result()
        stable_carriers()
        # The final child pass can itself be a reentrant mutation boundary.
        # Never return a report whose class-level authority changed after
        # the earlier denial checks. An extra denial sweep also catches
        # false-valued getters that retarget earlier result fields.
        for name in _DENIALS:
            if getattr(result, name) is not False:
                raise RegisteredBatchSetRejected("batch result gained authority")
            stable_result()
            stable_carriers()
        stable_result()
        stable_carriers()
        return result
    except (DisconnectedBatchRejected, RegisteredBatchReceiptRejected) as exc:
        raise RegisteredBatchSetRejected("registered batch set integrity denied") from exc
