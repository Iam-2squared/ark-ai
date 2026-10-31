"""Pure hypothetical terminal projection over a detached dependency wavefront.

A failed-step fixture is a caller assertion, never authenticated execution
evidence. This module never runs a tool, grants authority or advances Planner.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    verify_disconnected_batch_plan,
)
from .disconnected_batch_schedule import (
    DisconnectedBatchSchedule,
    verify_disconnected_batch_schedule,
)

_DOMAIN = b"ARK-detached-batch-terminal-projection-v1\0"
_STATES = frozenset(("SUCCEEDED", "FAILED", "BLOCKED"))
_FLAGS = (
    "dispatch_authorized", "write_authorized",
    "automatic_replay_authorized", "failure_claim_authenticated",
)


class DisconnectedBatchTerminalRejected(ValueError):
    """The hypothetical terminal scenario is invalid or changed."""


@dataclass(frozen=True, slots=True)
class DisconnectedBatchTerminalReceipt:
    request_id: str
    plan_digest: str
    schedule_digest: str
    failed_step_ids: tuple[str, ...]
    terminal_states: tuple[tuple[str, str], ...]
    projection_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def failure_claim_authenticated(self) -> bool:
        return False


_RECEIPT_TYPE = DisconnectedBatchTerminalReceipt


def _digest(payload: object) -> str:
    data = json.dumps(
        payload, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + data).hexdigest()


def project_disconnected_batch_terminals(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
    failed_step_ids: tuple[str, ...] = (),
) -> DisconnectedBatchTerminalReceipt:
    """Propagate synthetic failures to descendants without executing anything."""
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    if (
        type(failed_step_ids) is not tuple
        or len(failed_step_ids) > 24
        or any(type(item) is not str for item in failed_step_ids)
        or tuple(sorted(set(failed_step_ids))) != failed_step_ids
    ):
        raise DisconnectedBatchTerminalRejected("invalid hypothetical failure set")
    plan_epoch = (
        plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest,
    )
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    rows = tuple(
        (step, step.step_id, step.operation, step.canonical_args_json, step.depends_on)
        for step in plan.steps
    )
    by_id = {row[1]: row for row in rows}
    if any(item not in by_id for item in failed_step_ids):
        raise DisconnectedBatchTerminalRejected("unknown hypothetical failure step")

    def stable() -> None:
        if (
            any(now is not old for now, old in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest),
                plan_epoch, strict=True,
            ))
            or any(now is not old for now, old in zip(
                (schedule.request_id, schedule.plan_digest, schedule.waves,
                 schedule.schedule_digest), schedule_epoch, strict=True,
            ))
            or type(plan.steps) is not tuple
            or len(plan.steps) != len(rows)
            or any(
                step is not row[0] or any(
                    field is not before for field, before in zip(
                        (step.step_id, step.operation, step.canonical_args_json,
                         step.depends_on), row[1:], strict=True,
                    )
                )
                for step, row in zip(plan.steps, rows, strict=True)
            )
        ):
            raise DisconnectedBatchTerminalRejected("detached terminal inputs changed")

    stable()
    state: dict[str, str] = {}
    failures = set(failed_step_ids)
    for wave in schedule_epoch[2]:
        stable()
        before = state.copy()
        for step_id in wave:
            if step_id not in by_id or step_id in state:
                raise DisconnectedBatchTerminalRejected("invalid detached frontier")
            dependencies = by_id[step_id][4]
            if any(dep not in before for dep in dependencies):
                raise DisconnectedBatchTerminalRejected("unresolved detached dependency")
            if any(before[dep] != "SUCCEEDED" for dep in dependencies):
                if step_id in failures:
                    raise DisconnectedBatchTerminalRejected(
                        "blocked descendant cannot report executed failure"
                    )
                state[step_id] = "BLOCKED"
            else:
                state[step_id] = "FAILED" if step_id in failures else "SUCCEEDED"
        stable()
    if len(state) != len(rows) or set(state) != set(by_id):
        raise DisconnectedBatchTerminalRejected("incomplete terminal projection")
    ordered = tuple((row[1], state[row[1]]) for row in rows)
    stable()
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    stable()
    digest = _digest((plan_epoch[0], plan_epoch[3], schedule_epoch[3],
                      failed_step_ids, ordered))
    report = DisconnectedBatchTerminalReceipt(
        plan_epoch[0], plan_epoch[3], schedule_epoch[3],
        failed_step_ids, ordered, digest,
    )
    stable()
    if (
        type(report) is not _RECEIPT_TYPE
        or report.request_id is not plan_epoch[0]
        or report.plan_digest is not plan_epoch[3]
        or report.schedule_digest is not schedule_epoch[3]
        or report.failed_step_ids is not failed_step_ids
        or report.terminal_states is not ordered
        or report.projection_digest is not digest
        or any(getattr(report, flag) is not False for flag in _FLAGS)
    ):
        raise DisconnectedBatchTerminalRejected("terminal receipt changed")
    return report


def verify_disconnected_batch_terminals(
    receipt: DisconnectedBatchTerminalReceipt,
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
) -> None:
    """Recompute caller-declared hypothetical failures; never infer real outcomes."""
    if type(receipt) is not _RECEIPT_TYPE:
        raise DisconnectedBatchTerminalRejected("exact terminal receipt required")
    expected = project_disconnected_batch_terminals(
        plan, schedule, retained_digest=retained_digest,
        failed_step_ids=receipt.failed_step_ids,
    )

    def exact_fields() -> bool:
        # A synthetic receipt's __eq__ may be replaced. Verify each carrier
        # independently instead of treating Python equality as provenance.
        return (
            type(receipt) is _RECEIPT_TYPE
            and type(receipt.request_id) is str
            and receipt.request_id == expected.request_id
            and type(receipt.plan_digest) is str
            and receipt.plan_digest == expected.plan_digest
            and type(receipt.schedule_digest) is str
            and receipt.schedule_digest == expected.schedule_digest
            and type(receipt.failed_step_ids) is tuple
            and all(type(item) is str for item in receipt.failed_step_ids)
            and receipt.failed_step_ids == expected.failed_step_ids
            and type(receipt.terminal_states) is tuple
            and all(
                type(pair) is tuple and len(pair) == 2
                and type(pair[0]) is str and type(pair[1]) is str
                and pair[1] in _STATES
                for pair in receipt.terminal_states
            )
            and receipt.terminal_states == expected.terminal_states
            and type(receipt.projection_digest) is str
            and receipt.projection_digest == expected.projection_digest
        )

    if not exact_fields():
        raise DisconnectedBatchTerminalRejected("terminal projection integrity mismatch")
    for flag in _FLAGS:
        if getattr(receipt, flag) is not False:
            raise DisconnectedBatchTerminalRejected("terminal projection gained authority")
    # A denial getter may return False after reflectively rewriting the
    # receipt or caller plan. Recheck both after the last callback.
    if not exact_fields():
        raise DisconnectedBatchTerminalRejected("terminal projection changed after denial")
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    if not exact_fields():
        raise DisconnectedBatchTerminalRejected("terminal projection changed during review")
