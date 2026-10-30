"""Deterministic READ-only plan simulation; no ToolBackend or external dispatch.

This exercises the existing Planner, immutable ToolRegistry and PermissionGate
contracts through all DAG waves on a fresh *shadow* plan. It does not advance
the caller's plan, persist actions, authenticate time/consent, or grant authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .contracts import CapabilityGrant, PlanConflictError, StepState
from .disconnected_read_preflight import (
    DisconnectedReadPreflight,
    DisconnectedReadPreflightRejected,
    preview_registered_read_plan,
)
from .planner import PlanGraph
from .policy import PermissionGate
from .registry import ToolRegistry

_MAX_STEPS = 24
_REVIEW_TYPE = DisconnectedReadPreflight


class DisconnectedReadCycleRejected(ValueError):
    """A detached READ-only DAG could not be safely simulated."""


@dataclass(frozen=True, slots=True)
class DisconnectedReadCycleReceipt:
    topology_digest: str
    registry_revision: str
    wave_bound_step_hashes: tuple[tuple[str, ...], ...]
    final_status_digest: str
    fingerprint: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def external_result_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def authenticated_clock_or_consent(self) -> bool:
        return False


_RECEIPT_TYPE = DisconnectedReadCycleReceipt


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(b"ARK-offline-read-cycle-v1\0" + encoded).hexdigest()


def simulate_registered_read_cycle(
    plan: PlanGraph,
    registry: ToolRegistry,
    gate: PermissionGate,
    grants: tuple[CapabilityGrant, ...],
    *,
    observed_at_ms: int,
) -> DisconnectedReadCycleReceipt:
    """Simulate successful READ-only steps without invoking any backend.

    All steps start PENDING/revision 0. Every independent ready wave receives
    the same disconnected registry-bound grant preflight as a live planner
    would, but only a *shadow* PlanGraph transitions RUNNING -> SUCCEEDED.
    No synthetic success becomes evidence that a real-world action completed.
    """
    if (
        type(plan) is not PlanGraph
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(grants) is not tuple
        or not 1 <= len(plan.steps) <= _MAX_STEPS
    ):
        raise DisconnectedReadCycleRejected("exact bounded read-cycle inputs required")
    try:
        topology = plan.topology_digest()
        status = plan.status_digest()
        revision = registry.revision
        original_steps = tuple(plan.steps[key] for key in sorted(plan.steps))
        initial = plan.statuses()
    except (AttributeError, TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedReadCycleRejected("source plan is unstable") from exc
    if any(
        entry.state is not StepState.PENDING or entry.revision != 0
        for entry in initial.values()
    ):
        raise DisconnectedReadCycleRejected("only a fresh pending plan may be simulated")

    def source_stable() -> None:
        try:
            if (
                plan.topology_digest() != topology
                or plan.status_digest() != status
                or registry.revision != revision
                or any(
                    plan.steps[entry.step_id] is not entry
                    for entry in original_steps
                )
            ):
                raise DisconnectedReadCycleRejected("source plan changed during simulation")
        except (KeyError, TypeError, ValueError, PlanConflictError) as exc:
            if type(exc) is DisconnectedReadCycleRejected:
                raise
            raise DisconnectedReadCycleRejected("source plan became unstable") from exc

    source_stable()
    # No backend or journal is supplied to the shadow; PlanGraph only mutates
    # its own detached status mapping. Canonical ToolCall inputs are shared
    # strictly for identity, and validated again after every callback.
    try:
        shadow = PlanGraph(original_steps)
        if shadow.topology_digest() != topology or shadow.status_digest() != status:
            raise DisconnectedReadCycleRejected("shadow plan differs from source")
    except (TypeError, ValueError, PlanConflictError) as exc:
        if type(exc) is DisconnectedReadCycleRejected:
            raise
        raise DisconnectedReadCycleRejected("shadow plan construction failed") from exc

    waves: list[tuple[str, ...]] = []
    completed = 0
    for _ in range(len(original_steps)):
        source_stable()
        try:
            before = shadow.status_digest()
            review = preview_registered_read_plan(
                shadow, registry, gate, grants, observed_at_ms=observed_at_ms,
            )
        except (TypeError, ValueError, PlanConflictError, DisconnectedReadPreflightRejected) as exc:
            raise DisconnectedReadCycleRejected("READ wave preflight denied") from exc
        source_stable()
        if (
            type(review) is not _REVIEW_TYPE
            or review.topology_digest != topology
            or review.status_digest != before
            or review.registry_revision != revision
            or not review.ready_step_ids
            or len(review.ready_step_ids) != len(review.ready_bound_ids)
            or len(set(review.ready_step_ids)) != len(review.ready_step_ids)
            or review.dispatch_authorized is not False
        ):
            raise DisconnectedReadCycleRejected("READ wave receipt is not authoritative")

        wave: list[str] = []
        for step_id, bound_id in zip(
            review.ready_step_ids, review.ready_bound_ids, strict=True,
        ):
            source_stable()
            try:
                running = shadow.transition(
                    step_id, StepState.RUNNING, expected_revision=0,
                )
                done = shadow.transition(
                    step_id, StepState.SUCCEEDED, expected_revision=1,
                )
            except (KeyError, TypeError, ValueError, PlanConflictError) as exc:
                raise DisconnectedReadCycleRejected("shadow transition failed") from exc
            if (
                running.state is not StepState.RUNNING or running.revision != 1
                or done.state is not StepState.SUCCEEDED or done.revision != 2
                or running.step_id != step_id or done.step_id != step_id
            ):
                raise DisconnectedReadCycleRejected("shadow transition result changed")
            wave.append(_digest((step_id, bound_id)))
            completed += 1
            source_stable()
        waves.append(tuple(wave))
        if completed == len(original_steps):
            break

    if completed != len(original_steps):
        raise DisconnectedReadCycleRejected("READ graph did not finish inside step budget")
    source_stable()
    try:
        final = shadow.status_digest()
        states = shadow.statuses()
        if any(item.state is not StepState.SUCCEEDED for item in states.values()):
            raise DisconnectedReadCycleRejected("READ graph has an incomplete status")
    except (TypeError, ValueError, PlanConflictError) as exc:
        if type(exc) is DisconnectedReadCycleRejected:
            raise
        raise DisconnectedReadCycleRejected("shadow final state is invalid") from exc
    frozen_waves = tuple(waves)
    fingerprint = _digest((topology, status, revision, frozen_waves, final, observed_at_ms))
    source_stable()
    result = DisconnectedReadCycleReceipt(
        topology, revision, frozen_waves, final, fingerprint,
    )
    source_stable()
    if (
        type(result) is not _RECEIPT_TYPE
        or result.topology_digest is not topology
        or result.registry_revision is not revision
        or result.wave_bound_step_hashes is not frozen_waves
        or result.final_status_digest is not final
        or result.fingerprint is not fingerprint
    ):
        raise DisconnectedReadCycleRejected("simulation receipt changed")
    return result
