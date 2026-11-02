"""Review one disconnected Planner DAG step against a retained registered READ.

The journal has no act_ column; its external link remains untrusted caller
evidence. The plan and journal are inspected in separate transactions, so
this is NOT cross-store atomicity, actual execution, consent or retry authority.
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
from .disconnected_registered_fixture_join import RegisteredFixtureLink
from .disconnected_registered_receipt_review import (
    RegisteredReceiptReview,
    RegisteredReceiptReviewRejected,
    review_retained_registered_receipt,
)
from .disconnected_toolbox import DisconnectedToolRequest, DisconnectedToolResult
from .policy import PermissionGate
from .registry import ToolRegistry

_DOMAIN = b"ARK-disconnected-registered-batch-receipt-v1\0"
_DENIALS = (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "dependencies_completed_proven", "independent_custody_proven",
)


class RegisteredBatchReceiptRejected(ValueError):
    """The local plan and registered READ journal do not reconcile."""


@dataclass(frozen=True, slots=True)
class RegisteredBatchReceiptReview:
    step_id: str
    plan_digest: str
    schedule_digest: str
    wave_index: int
    action_request_id: str
    fixture_request_id: str
    link_sha256: str
    journal_count: int
    journal_tip_sha256: str
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


_RESULT = RegisteredBatchReceiptReview
# Original denial properties are captured at import, before any verifier may
# read an SQLite journal or invoke a caller-held registry/grant callback.
_ORIGINAL_DENIALS = tuple(getattr(_RESULT, name) for name in _DENIALS)


def _require_original_denials() -> None:
    if any(
        getattr(_RESULT, name) is not original
        for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
    ):
        raise RegisteredBatchReceiptRejected(
            "registered batch review changed after denial: descriptor replaced"
        )


def review_registered_batch_receipt(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    retained_plan_digest: str,
    journal: DisconnectedReadJournal,
    retained_journal: ReadJournalWitness,
    link: RegisteredFixtureLink,
    registry: ToolRegistry,
    gate: PermissionGate,
    call: ToolCall,
    grants: tuple[CapabilityGrant, ...],
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
    *,
    observed_at_ms: int,
) -> RegisteredBatchReceiptReview:
    """Correlate immutable diagnostic carriers without dispatching any tool."""
    _require_original_denials()
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(schedule) is not DisconnectedBatchSchedule
        or type(retained_plan_digest) is not str
        or type(step_id) is not str
        or type(plan.steps) is not tuple
    ):
        raise RegisteredBatchReceiptRejected("exact detached batch inputs required")
    plan_epoch = (
        plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest,
    )
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    try:
        steps = tuple(
            (item, item.step_id, item.operation, item.canonical_args_json,
             item.depends_on) for item in plan.steps
        )
    except AttributeError as exc:
        raise RegisteredBatchReceiptRejected("invalid batch steps") from exc

    def stable() -> None:
        _require_original_denials()
        if (
            type(plan) is not DisconnectedBatchPlan
            or type(schedule) is not DisconnectedBatchSchedule
            or any(a is not b for a, b in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json,
                 plan.plan_digest), plan_epoch, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (schedule.request_id, schedule.plan_digest, schedule.waves,
                 schedule.schedule_digest), schedule_epoch, strict=True,
            ))
            or type(plan.steps) is not tuple
            or len(plan.steps) != len(steps)
        ):
            raise RegisteredBatchReceiptRejected("detached plan changed during review")
        for item, name, operation, args, deps in steps:
            if (
                type(item.step_id) is not str
                or item.step_id is not name
                or item.operation is not operation
                or item.canonical_args_json is not args
                or item.depends_on is not deps
            ):
                raise RegisteredBatchReceiptRejected("detached step changed during review")

    def verify_plan() -> None:
        stable()
        verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
        stable()
        verify_disconnected_batch_schedule(
            schedule, plan, retained_digest=retained_plan_digest,
        )
        stable()

    try:
        verify_plan()
        matches = [
            (name, operation, args) for _, name, operation, args, _ in steps
            if name == step_id
        ]
        if len(matches) != 1 or type(request) is not DisconnectedToolRequest:
            raise RegisteredBatchReceiptRejected("batch step or fixture unavailable")
        if (
            matches[0][1] != request.operation
            or matches[0][2] != request.canonical_args_json
        ):
            raise RegisteredBatchReceiptRejected("READ fixture differs from DAG step")
        waves = [
            index for index, wave in enumerate(schedule.waves)
            if step_id in wave
        ]
        if len(waves) != 1:
            raise RegisteredBatchReceiptRejected("step wavefront unavailable")
        receipt = review_retained_registered_receipt(
            journal, retained_journal, link, registry, gate, call,
            grants, step_id, request, result, binding,
            observed_at_ms=observed_at_ms,
        )
        stable()
        if (
            type(receipt) is not RegisteredReceiptReview
            or receipt.step_id != step_id
            or receipt.fixture_request_id != request.request_id
            or receipt.action_request_id != call.request_id
        ):
            raise RegisteredBatchReceiptRejected("registered receipt changed")
        fields = (
            step_id, plan_epoch[3], schedule_epoch[3], waves[0],
            receipt.action_request_id, receipt.fixture_request_id,
            receipt.link_sha256, receipt.journal_count, receipt.journal_tip_sha256,
        )
        digest = hashlib.sha256(
            _DOMAIN + json.dumps(
                fields, ensure_ascii=True, separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        reviewed = _RESULT(*fields, digest)
        expected = (*fields, digest)

        def output_fields() -> tuple[object, ...]:
            return (
                reviewed.step_id, reviewed.plan_digest, reviewed.schedule_digest,
                reviewed.wave_index, reviewed.action_request_id,
                reviewed.fixture_request_id, reviewed.link_sha256,
                reviewed.journal_count, reviewed.journal_tip_sha256,
                reviewed.review_sha256,
            )

        def stable_output() -> None:
            _require_original_denials()
            if (
                type(reviewed) is not _RESULT
                or any(a is not b for a, b in zip(
                    output_fields(), expected, strict=True,
                ))
            ):
                raise RegisteredBatchReceiptRejected(
                    "registered batch review gained authority or changed"
                )
            for key in _DENIALS:
                if getattr(reviewed, key) is not False:
                    raise RegisteredBatchReceiptRejected(
                        "registered batch review gained authority or changed"
                    )
                # A denial getter is a callback boundary. Recheck both the
                # original method object and every identity-bound result field
                # after *each* getter, including the final one.
                _require_original_denials()
                if any(a is not b for a, b in zip(
                    output_fields(), expected, strict=True,
                )):
                    raise RegisteredBatchReceiptRejected(
                        "registered batch review changed after denial"
                    )

        stable_output()
        verify_plan()
        stable_output()
        # This second independent SQLite read detects later local drift; it
        # cannot create a shared transaction or authenticate prior actors.
        again = review_retained_registered_receipt(
            journal, retained_journal, link, registry, gate, call,
            grants, step_id, request, result, binding,
            observed_at_ms=observed_at_ms,
        )
        if (
            type(again) is not RegisteredReceiptReview
            or (again.step_id, again.action_request_id, again.fixture_request_id,
                again.link_sha256, again.journal_count, again.journal_tip_sha256)
            != (fields[0], fields[4], fields[5], fields[6], fields[7], fields[8])
        ):
            raise RegisteredBatchReceiptRejected("registered journal witness drifted")
        verify_plan()
        stable_output()
        return reviewed
    except (DisconnectedBatchRejected, RegisteredReceiptReviewRejected) as exc:
        raise RegisteredBatchReceiptRejected(
            "detached registered batch review denied"
        ) from exc
