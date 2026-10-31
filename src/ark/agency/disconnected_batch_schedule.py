"""Deterministic dependency wavefronts for *detached*, non-executing batch plans.

This is a local data-only preview. No ToolRegistry lookup, permission grant,
backend dispatch, trusted clock, account connection or external execution occurs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    DisconnectedBatchRejected,
    verify_disconnected_batch_plan,
)

_DOMAIN = b"ARK-detached-batch-wavefront-v1\0"


@dataclass(frozen=True, slots=True)
class DisconnectedBatchSchedule:
    request_id: str
    plan_digest: str
    waves: tuple[tuple[str, ...], ...]
    schedule_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def parallel_execution_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False


def _wavefronts(plan: DisconnectedBatchPlan) -> tuple[tuple[str, ...], ...]:
    remaining = list(plan.steps)
    completed: set[str] = set()
    waves: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            step.step_id for step in remaining
            if all(previous in completed for previous in step.depends_on)
        )
        if not ready:
            raise DisconnectedBatchRejected("batch has an unsatisfied dependency cycle")
        waves.append(ready)
        completed.update(ready)
        ready_set = set(ready)
        remaining = [step for step in remaining if step.step_id not in ready_set]
        if len(waves) > 24:
            raise DisconnectedBatchRejected("detached batch wave budget exceeded")
    return tuple(waves)


def _digest(request_id: str, plan_digest: str, waves: tuple[tuple[str, ...], ...]) -> str:
    canonical = json.dumps(
        {"plan_digest": plan_digest, "request_id": request_id, "waves": waves},
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + canonical).hexdigest()


def build_disconnected_batch_schedule(
    plan: DisconnectedBatchPlan, *, retained_digest: str,
) -> DisconnectedBatchSchedule:
    """Produce maximal ready-at-start waves from independently verified plan bytes.

    Waves contain step IDs, not executable calls. Steps in one wave have no
    dependencies on another step in that wave. No concurrency is launched.
    """
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    request_id, plan_digest, steps = plan.request_id, plan.plan_digest, plan.steps
    waves = _wavefronts(plan)
    # A compromised local caller can reflectively mutate a frozen plan while
    # building the preview. Revalidate before publishing any schedule identity.
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    if (
        plan.request_id is not request_id or plan.plan_digest is not plan_digest
        or plan.steps is not steps
    ):
        raise DisconnectedBatchRejected("batch changed during wavefront construction")
    digest = _digest(request_id, plan_digest, waves)
    report = DisconnectedBatchSchedule(request_id, plan_digest, waves, digest)
    if (
        type(report) is not DisconnectedBatchSchedule
        or report.request_id is not request_id
        or report.plan_digest is not plan_digest
        or report.waves is not waves
        or report.schedule_digest is not digest
        or any(type(getattr(report, name)) is not bool or getattr(report, name)
               for name in (
                   "dispatch_authorized", "parallel_execution_authorized",
                   "write_authorized", "replay_authorized",
               ))
    ):
        raise DisconnectedBatchRejected("batch schedule cannot authorize actions")
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    return report


def verify_disconnected_batch_schedule(
    schedule: DisconnectedBatchSchedule,
    plan: DisconnectedBatchPlan,
    *,
    retained_digest: str,
) -> None:
    """Check a detached schedule against an independently retained plan digest."""
    if type(schedule) is not DisconnectedBatchSchedule:
        raise DisconnectedBatchRejected("exact detached schedule type required")
    expected = build_disconnected_batch_schedule(plan, retained_digest=retained_digest)

    def exact_fields() -> bool:
        # Do not delegate integrity to a dataclass __eq__ that can be replaced
        # or can run arbitrary caller-controlled callbacks.
        return (
            type(schedule) is DisconnectedBatchSchedule
            and type(schedule.request_id) is str
            and schedule.request_id == expected.request_id
            and type(schedule.plan_digest) is str
            and schedule.plan_digest == expected.plan_digest
            and type(schedule.schedule_digest) is str
            and schedule.schedule_digest == expected.schedule_digest
            and type(schedule.waves) is tuple
            and len(schedule.waves) == len(expected.waves)
            and all(
                type(wave) is tuple
                and all(type(step) is str for step in wave)
                for wave in schedule.waves
            )
            and schedule.waves == expected.waves
        )

    if not exact_fields():
        raise DisconnectedBatchRejected("detached batch schedule integrity mismatch")
    for name in (
        "dispatch_authorized", "parallel_execution_authorized",
        "write_authorized", "replay_authorized",
    ):
        if getattr(schedule, name) is not False:
            raise DisconnectedBatchRejected("detached batch schedule integrity mismatch")
    # Denial-only properties are callbacks: a False result can still mutate a
    # frozen dataclass reflectively. Recheck after the final getter and after
    # the independently retained plan is revalidated.
    if not exact_fields():
        raise DisconnectedBatchRejected("detached batch schedule changed after denial")
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    if not exact_fields():
        raise DisconnectedBatchRejected("detached batch schedule changed during review")
