"""Failure-aware detached wavefront fixture; never a real ToolBackend action.

Caller-supplied failure IDs are hypothetical and unauthenticated. Successful
steps run only the fixed, memory-only fixture toolbox; blocked descendants
never run, and no receipt grants permission, consent or external completion.
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
from .disconnected_batch_terminal_projection import (
    DisconnectedBatchTerminalReceipt,
    project_disconnected_batch_terminals,
    verify_disconnected_batch_terminals,
)
from .disconnected_fixture_binding import (
    DisconnectedFixtureBinding,
    DisconnectedFixtureBindingRejected,
    bind_disconnected_fixture_result,
)
from .disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    DisconnectedToolResult,
    execute_disconnected_fixture_tool,
)

_DOMAIN = b"ARK-detached-failure-fixture-v1\0"
_TOOL_DOMAIN = b"ARK-disconnected-toolbox-v1\0"
_FLAGS = (
    "dispatch_authorized", "write_authorized", "automatic_replay_authorized",
    "failure_authenticated", "external_outcome_verified",
)


class DisconnectedFailureFixtureRejected(ValueError):
    """Reject a changed or inconsistent synthetic dependency scenario."""


@dataclass(frozen=True, slots=True)
class DisconnectedFailureFixtureReceipt:
    request_id: str
    plan_digest: str
    schedule_digest: str
    projection_digest: str
    failed_step_ids: tuple[str, ...]
    terminal_states: tuple[tuple[str, str], ...]
    result_digests: tuple[tuple[str, str], ...]
    fixture_digest: str

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
    def failure_authenticated(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False


_RECEIPT_TYPE = DisconnectedFailureFixtureReceipt
_RESULT_TYPE = DisconnectedToolResult


def _digest(payload: object) -> str:
    raw = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + raw).hexdigest()


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise DisconnectedFailureFixtureRejected("duplicate synthetic result JSON key")
        output[key] = value
    return output


def simulate_disconnected_failure_fixture(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
    failed_step_ids: tuple[str, ...] = (),
) -> DisconnectedFailureFixtureReceipt:
    """Simulate a fixed failure mask with no side effects or parallel dispatch."""
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    projection = project_disconnected_batch_terminals(
        plan, schedule, retained_digest=retained_digest,
        failed_step_ids=failed_step_ids,
    )
    # The projection is a callback result, not a source of authority.
    # Recompute with the independently imported terminal verifier before
    # even a disconnected mock result is permitted.
    if (
        type(projection) is not DisconnectedBatchTerminalReceipt
        or projection.failed_step_ids is not failed_step_ids
        or projection.dispatch_authorized is not False
        or projection.write_authorized is not False
        or projection.automatic_replay_authorized is not False
        or projection.failure_claim_authenticated is not False
    ):
        raise DisconnectedFailureFixtureRejected(
            "hypothetical terminal projection gained authority"
        )
    try:
        verify_disconnected_batch_terminals(
            projection, plan, schedule, retained_digest=retained_digest,
        )
    except (TypeError, ValueError) as exc:
        raise DisconnectedFailureFixtureRejected(
            "hypothetical terminal projection mismatch"
        ) from exc
    plan_epoch = (
        plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest,
    )
    schedule_epoch = (
        schedule.request_id, schedule.plan_digest, schedule.waves,
        schedule.schedule_digest,
    )
    records = tuple(
        (step, step.step_id, step.operation, step.canonical_args_json, step.depends_on)
        for step in plan.steps
    )
    projection_epoch = (
        projection.request_id, projection.plan_digest,
        projection.schedule_digest, projection.failed_step_ids,
        projection.terminal_states, projection.projection_digest,
    )

    def stable() -> None:
        if (
            any(a is not b for a, b in zip(
                (plan.request_id, plan.steps, plan.canonical_plan_json, plan.plan_digest),
                plan_epoch, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (schedule.request_id, schedule.plan_digest, schedule.waves,
                 schedule.schedule_digest), schedule_epoch, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (projection.request_id, projection.plan_digest,
                 projection.schedule_digest, projection.failed_step_ids,
                 projection.terminal_states, projection.projection_digest),
                projection_epoch, strict=True,
            ))
            or type(projection) is not DisconnectedBatchTerminalReceipt
            or projection.dispatch_authorized is not False
            or projection.write_authorized is not False
            or projection.automatic_replay_authorized is not False
            or projection.failure_claim_authenticated is not False
            or type(plan.steps) is not tuple
            or len(plan.steps) != len(records)
            or any(
                step is not before[0] or any(
                    a is not b for a, b in zip(
                        (step.step_id, step.operation, step.canonical_args_json,
                         step.depends_on), before[1:], strict=True,
                    )
                )
                for step, before in zip(plan.steps, records, strict=True)
            )
        ):
            raise DisconnectedFailureFixtureRejected("detached scenario changed")

    stable()
    state_by_id = dict(projection.terminal_states)
    records_by_id = {record[1]: record for record in records}
    successful: list[tuple[str, str]] = []
    seen: set[str] = set()
    for wave in schedule.waves:
        stable()
        for step_id in wave:
            stable()
            if step_id in seen or step_id not in records_by_id:
                raise DisconnectedFailureFixtureRejected("invalid fixture frontier")
            seen.add(step_id)
            state = state_by_id[step_id]
            if state in ("FAILED", "BLOCKED"):
                continue  # Never call even the disconnected fixture for these steps.
            if state != "SUCCEEDED":
                raise DisconnectedFailureFixtureRejected("unknown terminal state")
            _, _, operation, args, _ = records_by_id[step_id]
            request = DisconnectedToolRequest(plan_epoch[0], operation, args)
            try:
                result = execute_disconnected_fixture_tool(request)
            except (DisconnectedToolRejected, TypeError, ValueError) as exc:
                raise DisconnectedFailureFixtureRejected(
                    "disconnected successful fixture rejected"
                ) from exc
            stable()
            result_epoch = (
                result.request_id, result.operation, result.input_digest,
                result.canonical_result_json, result.result_digest,
            )
            if (
                type(result) is not _RESULT_TYPE
                or type(result.request_id) is not str
                or result.request_id != plan_epoch[0]
                or type(result.operation) is not str
                or result.operation != operation
                or type(result.input_digest) is not str
                or result.input_digest != hashlib.sha256(
                    _TOOL_DOMAIN + args.encode("utf-8")
                ).hexdigest()
                or type(result.result_digest) is not str
                or type(result.canonical_result_json) is not str
                or result.dispatch_authorized is not False
                or result.automatic_replay_authorized is not False
                or result.external_outcome_known is not False
            ):
                raise DisconnectedFailureFixtureRejected(
                    "synthetic result identity or authority changed"
                )
            try:
                raw = result.canonical_result_json.encode("utf-8", "strict")
                parsed = json.loads(result.canonical_result_json, object_pairs_hook=_unique)
                canonical = json.dumps(
                    parsed, sort_keys=True, ensure_ascii=True,
                    separators=(",", ":"), allow_nan=False,
                )
            except DisconnectedFailureFixtureRejected:
                raise
            except (UnicodeError, TypeError, ValueError, RecursionError) as exc:
                raise DisconnectedFailureFixtureRejected(
                    "noncanonical synthetic result"
                ) from exc
            if (
                type(parsed) is not dict
                or not 0 < len(raw) <= 16_384
                or canonical != result.canonical_result_json
                or result.result_digest != hashlib.sha256(
                    _TOOL_DOMAIN + operation.encode("ascii") + b"\0" + raw
                ).hexdigest()
            ):
                raise DisconnectedFailureFixtureRejected(
                    "synthetic result content mismatch"
                )
            # The toolbox's SHA binds operation/result bytes but does not
            # prove the claimed result actually follows from the inputs.
            # A second fixed fixture implementation rederives it without
            # executing a real tool, and binds the synthetic request ID.
            try:
                bound = bind_disconnected_fixture_result(request, result)
            except (DisconnectedFixtureBindingRejected, TypeError, ValueError) as exc:
                raise DisconnectedFailureFixtureRejected(
                    "synthetic recomputation mismatch"
                ) from exc
            stable()
            if (
                type(bound) is not DisconnectedFixtureBinding
                or bound.request_id != plan_epoch[0]
                or bound.operation != operation
                or bound.input_digest != result_epoch[2]
                or bound.result_digest != result_epoch[4]
                or type(bound.request_bound_digest) is not str
                or len(bound.request_bound_digest) != 64
                or bound.dispatch_authorized is not False
                or bound.external_outcome_verified is not False
                or bound.automatic_replay_authorized is not False
                or any(a is not b for a, b in zip(
                    (result.request_id, result.operation, result.input_digest,
                     result.canonical_result_json, result.result_digest),
                    result_epoch, strict=True,
                ))
            ):
                raise DisconnectedFailureFixtureRejected(
                    "synthetic request-bound fixture changed"
                )
            successful.append((step_id, bound.request_bound_digest))
            stable()
    if seen != set(records_by_id) or len(successful) != sum(
        state == "SUCCEEDED" for state in state_by_id.values()
    ):
        raise DisconnectedFailureFixtureRejected("incomplete synthetic fixture")
    stable()
    verify_disconnected_batch_plan(plan, retained_digest=retained_digest)
    verify_disconnected_batch_schedule(schedule, plan, retained_digest=retained_digest)
    stable()
    digest = _digest((
        plan_epoch[0], plan_epoch[3], schedule_epoch[3],
        projection.projection_digest, failed_step_ids,
        projection.terminal_states, tuple(successful),
    ))
    receipt = DisconnectedFailureFixtureReceipt(
        plan_epoch[0], plan_epoch[3], schedule_epoch[3],
        projection.projection_digest, failed_step_ids,
        projection.terminal_states, tuple(successful), digest,
    )
    stable()
    if (
        type(receipt) is not _RECEIPT_TYPE
        or receipt.request_id is not plan_epoch[0]
        or receipt.plan_digest is not plan_epoch[3]
        or receipt.schedule_digest is not schedule_epoch[3]
        or receipt.projection_digest is not projection.projection_digest
        or receipt.failed_step_ids is not failed_step_ids
        or receipt.terminal_states is not projection.terminal_states
        or receipt.fixture_digest is not digest
        or any(getattr(receipt, key) is not False for key in _FLAGS)
    ):
        raise DisconnectedFailureFixtureRejected("synthetic receipt changed")
    return receipt


def verify_disconnected_failure_fixture(
    receipt: DisconnectedFailureFixtureReceipt,
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_digest: str,
) -> None:
    """Recompute a hypothetical failure fixture, never authenticate outcomes."""
    if type(receipt) is not _RECEIPT_TYPE:
        raise DisconnectedFailureFixtureRejected("exact synthetic receipt required")
    expected = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=retained_digest,
        failed_step_ids=receipt.failed_step_ids,
    )
    if (
        type(receipt.failed_step_ids) is not tuple
        or type(receipt.terminal_states) is not tuple
        or type(receipt.result_digests) is not tuple
        or any(
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or type(pair[1]) is not str
            for pair in receipt.terminal_states + receipt.result_digests
        )
        or type(receipt.fixture_digest) is not str
        or receipt != expected
        or any(getattr(receipt, key) is not False for key in _FLAGS)
    ):
        raise DisconnectedFailureFixtureRejected("synthetic receipt mismatch")
