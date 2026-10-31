"""Detached batch fixture cycle: deterministic in-memory calculations only.

This is deliberately NOT ToolBackend, permission, consent, clock, audit or
proof of real-world completion. It cannot dispatch or replay any action.
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
from .disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    DisconnectedToolResult,
    execute_disconnected_fixture_tool,
)

_DOMAIN = b"ARK-detached-batch-fixture-cycle-v1\0"
_TOOL_DOMAIN = b"ARK-disconnected-toolbox-v1\0"
_RECEIPT_FLAGS = (
    "dispatch_authorized", "parallel_execution_authorized",
    "write_authorized", "automatic_replay_authorized",
    "external_outcome_verified", "authenticated_consent",
)


class DisconnectedBatchCycleRejected(ValueError):
    """Fail closed on a changed detached plan, schedule or mock result."""


@dataclass(frozen=True, slots=True)
class DisconnectedBatchCycleReceipt:
    request_id: str
    plan_digest: str
    schedule_digest: str
    wave_result_hashes: tuple[tuple[str, ...], ...]
    cycle_digest: str

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
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def authenticated_consent(self) -> bool:
        return False


_RECEIPT_TYPE = DisconnectedBatchCycleReceipt
_RESULT_TYPE = DisconnectedToolResult


def _digest(payload: object) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + canonical).hexdigest()


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DisconnectedBatchCycleRejected("duplicate mock result JSON key")
        result[key] = value
    return result


def simulate_disconnected_batch_fixture_cycle(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
) -> DisconnectedBatchCycleReceipt:
    """Evaluate fixed detached fixture operations in wave order, without dispatch.

    No concurrency, actual ToolRegistry, PermissionGate, external observations,
    persistence, claims of action completion, or inferred user approval.
    """
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    plan_epoch = (
        plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest,
    )
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    row_epoch = tuple(
        (step, step.step_id, step.operation, step.canonical_args_json, step.depends_on)
        for step in plan.steps
    )

    def check_epoch() -> None:
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
            or len(plan.steps) != len(row_epoch)
            or any(
                step is not old_step or any(
                    current is not saved for current, saved in zip(
                        (step.step_id, step.operation, step.canonical_args_json,
                         step.depends_on), record[1:], strict=True,
                    )
                )
                for step, record in zip(plan.steps, row_epoch, strict=True)
                for old_step in (record[0],)
            )
        ):
            raise DisconnectedBatchCycleRejected("detached batch changed during cycle")

    check_epoch()
    by_id = {record[1]: record for record in row_epoch}
    completed: set[str] = set()
    wave_hashes: list[tuple[str, ...]] = []
    for wave in schedule_epoch[2]:
        check_epoch()
        before = completed.copy()
        if type(wave) is not tuple or not wave:
            raise DisconnectedBatchCycleRejected("invalid detached wave")
        produced: list[str] = []
        for step_id in wave:
            check_epoch()
            if step_id not in by_id:
                raise DisconnectedBatchCycleRejected("unknown detached step")
            step, original_id, operation, raw, parents = by_id[step_id]
            if step_id in completed or not set(parents).issubset(before):
                raise DisconnectedBatchCycleRejected("unsafe detached dependency frontier")
            request = DisconnectedToolRequest(plan_epoch[0], operation, raw)
            try:
                result = execute_disconnected_fixture_tool(request)
            except (DisconnectedToolRejected, TypeError, ValueError) as exc:
                raise DisconnectedBatchCycleRejected("detached fixture step rejected") from exc
            check_epoch()
            if (
                type(result) is not _RESULT_TYPE
                or type(result.request_id) is not str
                or result.request_id != plan_epoch[0]
                or type(result.operation) is not str
                or result.operation != operation
                or type(result.input_digest) is not str
                or result.input_digest != hashlib.sha256(
                    _TOOL_DOMAIN + raw.encode("utf-8")
                ).hexdigest()
                or type(result.canonical_result_json) is not str
                or type(result.result_digest) is not str
            ):
                raise DisconnectedBatchCycleRejected("detached fixture identity mismatch")
            try:
                result_bytes = result.canonical_result_json.encode("utf-8", "strict")
                parsed = json.loads(
                    result.canonical_result_json, object_pairs_hook=_unique_pairs,
                )
                canonical = json.dumps(
                    parsed, ensure_ascii=True, sort_keys=True,
                    separators=(",", ":"), allow_nan=False,
                )
            except DisconnectedBatchCycleRejected:
                raise
            except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
                raise DisconnectedBatchCycleRejected("noncanonical detached result") from exc
            if (
                type(parsed) is not dict
                or not 0 < len(result_bytes) <= 16_384
                or canonical != result.canonical_result_json
                or result.result_digest != hashlib.sha256(
                    _TOOL_DOMAIN + operation.encode("ascii") + b"\0" + result_bytes
                ).hexdigest()
                or result.dispatch_authorized is not False
                or result.automatic_replay_authorized is not False
                or result.external_outcome_known is not False
            ):
                raise DisconnectedBatchCycleRejected("detached result or authority changed")
            produced.append(_digest((original_id, operation, result.input_digest,
                                     result.result_digest)))
            check_epoch()
        completed.update(wave)
        wave_hashes.append(tuple(produced))
    if completed != set(by_id) or len(completed) != len(row_epoch):
        raise DisconnectedBatchCycleRejected("incomplete detached fixture cycle")
    check_epoch()
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    check_epoch()
    frozen = tuple(wave_hashes)
    digest = _digest((plan_epoch[0], plan_epoch[3], schedule_epoch[3], frozen))
    receipt = DisconnectedBatchCycleReceipt(
        plan_epoch[0], plan_epoch[3], schedule_epoch[3], frozen, digest,
    )
    check_epoch()
    if (
        type(receipt) is not _RECEIPT_TYPE
        or receipt.request_id is not plan_epoch[0]
        or receipt.plan_digest is not plan_epoch[3]
        or receipt.schedule_digest is not schedule_epoch[3]
        or receipt.wave_result_hashes is not frozen
        or receipt.cycle_digest is not digest
        or any(getattr(receipt, key) is not False for key in _RECEIPT_FLAGS)
    ):
        raise DisconnectedBatchCycleRejected("detached cycle receipt changed")
    return receipt


def verify_disconnected_batch_fixture_cycle(
    receipt: DisconnectedBatchCycleReceipt,
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
) -> None:
    """Independently rerun only in-memory fixtures, never a real action."""
    if type(receipt) is not _RECEIPT_TYPE:
        raise DisconnectedBatchCycleRejected("exact detached receipt type required")
    expected = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=retained_digest,
    )
    if (
        type(receipt.request_id) is not str
        or type(receipt.plan_digest) is not str
        or type(receipt.schedule_digest) is not str
        or type(receipt.cycle_digest) is not str
        or type(receipt.wave_result_hashes) is not tuple
        or any(
            type(wave) is not tuple or any(type(item) is not str for item in wave)
            for wave in receipt.wave_result_hashes
        )
        or receipt != expected
        or any(getattr(receipt, key) is not False for key in _RECEIPT_FLAGS)
    ):
        raise DisconnectedBatchCycleRejected("detached cycle receipt integrity mismatch")
