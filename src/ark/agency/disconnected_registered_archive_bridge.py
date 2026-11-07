"""Read-only join of a persisted mock DAG cycle and registered READ journals.

Both inputs must independently match the exact same detached plan/schedule.
Separate file and SQLite reads are NOT an atomic snapshot, authenticated
provenance, real action completion, user consent or a replay authorization.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .disconnected_batch_cycle_archive import (
    ArchivedDisconnectedBatchCycle,
    DisconnectedBatchArchiveRejected,
    review_disconnected_batch_fixture_cycle_archive,
)
from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    DisconnectedBatchRejected,
    DisconnectedBatchStep,
)
from .disconnected_batch_schedule import DisconnectedBatchSchedule
from .disconnected_registered_batch_receipt_set import (
    RegisteredBatchSetRejected,
    RegisteredBatchSetReview,
    RegisteredBatchStepEvidence,
    review_registered_batch_receipt_set,
)
from .policy import PermissionGate
from .registry import ToolRegistry

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-registered-cycle-archive-join-v1\0"
_DENIED = (
    "backend_dispatched", "write_authorized", "automatic_replay_authorized",
    "consent_authenticated", "independent_custody_proven",
    "external_outcome_proven",
)


class RegisteredArchiveBridgeRejected(ValueError):
    """Local registered READs do not match the retained mock cycle archive."""


@dataclass(frozen=True, slots=True)
class RegisteredArchiveBridgeReview:
    plan_digest: str
    schedule_digest: str
    cycle_file_sha256: str
    cycle_digest: str
    registered_review_sha256: str
    step_count: int
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
    def consent_authenticated(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def external_outcome_proven(self) -> bool:
        return False


_REPORT = RegisteredArchiveBridgeReview
_ARCHIVE = ArchivedDisconnectedBatchCycle
_REGISTERED = RegisteredBatchSetReview
_ARCHIVE_DENIED = (
    "external_dispatch_authorized", "write_authorized",
    "automatic_replay_authorized", "real_outcome_proven",
)
_REGISTERED_DENIED = (
    "backend_dispatched", "write_authorized",
    "automatic_replay_authorized", "dependencies_completed_proven",
    "independent_custody_proven",
)
# Retain imported property definitions, not an arbitrary False-only callback
# substituted before this composite review begins.
_ORIGINAL_REPORT_DENIALS = tuple(getattr(_REPORT, key) for key in _DENIED)
_ORIGINAL_ARCHIVE_DENIALS = tuple(
    getattr(_ARCHIVE, key) for key in _ARCHIVE_DENIED
)
_ORIGINAL_REGISTERED_DENIALS = tuple(
    getattr(_REGISTERED, key) for key in _REGISTERED_DENIED
)


def _check_original_denials() -> None:
    for cls, names, originals in (
        (_REPORT, _DENIED, _ORIGINAL_REPORT_DENIALS),
        (_ARCHIVE, _ARCHIVE_DENIED, _ORIGINAL_ARCHIVE_DENIALS),
        (_REGISTERED, _REGISTERED_DENIED, _ORIGINAL_REGISTERED_DENIALS),
    ):
        if any(
            getattr(cls, name) is not original
            for name, original in zip(names, originals, strict=True)
        ):
            raise RegisteredArchiveBridgeRejected(
                "detached registered archive authority definition changed"
            )


def review_registered_cycle_archive_bridge(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    evidence: tuple[RegisteredBatchStepEvidence, ...],
    registry: ToolRegistry,
    gate: PermissionGate,
    *,
    retained_plan_digest: str,
    path: Path,
    retained_file_sha256: str,
    observed_at_ms: int,
) -> RegisteredArchiveBridgeReview:
    """Reconcile offline mock-only durable receipts, with no ToolBackend action."""
    if (
        type(plan) is not DisconnectedBatchPlan
        or type(schedule) is not DisconnectedBatchSchedule
        or type(evidence) is not tuple
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(retained_plan_digest) is not str
        or _SHA.fullmatch(retained_plan_digest) is None
        or type(retained_file_sha256) is not str
        or _SHA.fullmatch(retained_file_sha256) is None
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms < (1 << 63)
        or type(plan.steps) is not tuple
        or not 1 <= len(plan.steps) == len(evidence) <= 24
    ):
        raise RegisteredArchiveBridgeRejected("exact bounded detached join inputs required")

    _check_original_denials()
    plan_epoch = (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest)
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    original_evidence = tuple(evidence)
    # Plan steps and registered receipt carriers are frozen dataclasses, but
    # object.__setattr__ can still replace their fields during a reviewer
    # callback. Retaining only the outer tuple identity is insufficient.
    step_carriers = tuple(plan.steps)
    step_fields = tuple(
        (step.step_id, step.operation, step.canonical_args_json, step.depends_on)
        for step in step_carriers
    )
    evidence_fields = tuple(
        (item.journal, item.retained_journal, item.link, item.call,
         item.grants, item.request, item.result, item.binding)
        for item in original_evidence
    )
    waves = tuple(schedule.waves)

    def stable() -> None:
        _check_original_denials()
        if (
            type(plan) is not DisconnectedBatchPlan
            or type(schedule) is not DisconnectedBatchSchedule
            or type(evidence) is not tuple
            or len(evidence) != len(original_evidence)
            or any(now is not original for now, original in zip(
                evidence, original_evidence, strict=True,
            ))
            or type(plan.steps) is not tuple
            or any(
                type(step) is not DisconnectedBatchStep
                or step is not carrier
                or any(value is not original for value, original in zip((
                    step.step_id, step.operation, step.canonical_args_json,
                    step.depends_on,
                ), fields, strict=True))
                for step, carrier, fields in zip(
                    plan.steps, step_carriers, step_fields, strict=True,
                )
            )
            or type(schedule.waves) is not tuple
            or any(wave is not original for wave, original in zip(
                schedule.waves, waves, strict=True,
            ))
            or any(
                type(item) is not RegisteredBatchStepEvidence
                or any(value is not original for value, original in zip((
                    item.journal, item.retained_journal, item.link, item.call,
                    item.grants, item.request, item.result, item.binding,
                ), fields, strict=True))
                for item, fields in zip(
                    evidence, evidence_fields, strict=True,
                )
            )
            or any(now is not original for now, original in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest),
                plan_epoch, strict=True,
            ))
            or any(now is not original for now, original in zip(
                (schedule.request_id, schedule.plan_digest,
                 schedule.waves, schedule.schedule_digest),
                schedule_epoch, strict=True,
            ))
        ):
            raise RegisteredArchiveBridgeRejected("detached join source changed")

    def inspect() -> tuple[object, ...]:
        stable()
        archived = review_disconnected_batch_fixture_cycle_archive(
            plan, schedule, retained_plan_digest=retained_plan_digest,
            path=path, retained_file_sha256=retained_file_sha256,
        )
        stable()
        registered = review_registered_batch_receipt_set(
            plan, schedule, retained_plan_digest, evidence, registry, gate,
            observed_at_ms=observed_at_ms,
        )
        stable()
        if (
            type(archived) is not _ARCHIVE
            or type(registered) is not _REGISTERED
            or archived.request_id != plan_epoch[0]
            or archived.plan_digest != plan_epoch[3]
            or registered.plan_digest != plan_epoch[3]
            or registered.schedule_digest != schedule_epoch[3]
            or archived.file_sha256 != retained_file_sha256
            or type(archived.cycle_digest) is not str
            or _SHA.fullmatch(archived.cycle_digest) is None
            or type(registered.review_sha256) is not str
            or _SHA.fullmatch(registered.review_sha256) is None
            or type(registered.step_receipts) is not tuple
            or len(registered.step_receipts) != len(plan_epoch[1])
            or any(getattr(archived, key) is not False for key in _ARCHIVE_DENIED)
            or any(getattr(registered, key) is not False for key in _REGISTERED_DENIED)
        ):
            raise RegisteredArchiveBridgeRejected("detached evidence gained authority")
        stable()
        return (
            plan_epoch[3], schedule_epoch[3], retained_file_sha256,
            archived.cycle_digest, registered.review_sha256,
            len(registered.step_receipts),
        )

    try:
        fields = inspect()
        digest = hashlib.sha256(
            _DOMAIN + json.dumps(
                fields, separators=(",", ":"), ensure_ascii=True,
            ).encode("ascii")
        ).hexdigest()
        report = _REPORT(*fields, digest)
        pinned = (*fields, digest)
        descriptors = _ORIGINAL_REPORT_DENIALS

        def stable_report() -> None:
            if (
                type(report) is not _REPORT
                or any(now is not original for now, original in zip((
                    report.plan_digest, report.schedule_digest,
                    report.cycle_file_sha256, report.cycle_digest,
                    report.registered_review_sha256, report.step_count,
                    report.join_sha256,
                ), pinned, strict=True))
                or any(getattr(_REPORT, key) is not original for key, original in zip(
                    _DENIED, descriptors, strict=True,
                ))
            ):
                raise RegisteredArchiveBridgeRejected("detached join report changed")
            stable()

        stable_report()
        for key in _DENIED:
            if getattr(report, key) is not False:
                raise RegisteredArchiveBridgeRejected("detached join gained authority")
            stable_report()
        if inspect() != fields:
            raise RegisteredArchiveBridgeRejected("detached join sources drifted")
        stable_report()
        return report
    except (
        DisconnectedBatchArchiveRejected, DisconnectedBatchRejected,
        RegisteredBatchSetRejected,
    ) as exc:
        raise RegisteredArchiveBridgeRejected("detached archive or READ review rejected") from exc
