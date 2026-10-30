"""Fail-closed, disconnected Planner/Registry/PermissionGate READ preflight.

This joins already-tested local contracts without calling a backend. An observed
clock value and caller-provided grants have no independent authenticity. The
content-free result never confers permission to dispatch a real action.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .contracts import CapabilityGrant, Effect, PermissionDenied, PlanConflictError, StepState
from .planner import PlanGraph
from .policy import PermissionGate
from .registry import BoundAction, ToolRegistry

_MAX_STEPS = 24
_MAX_GRANTS = 128
_MAX_MS = 2**63 - 1


class DisconnectedReadPreflightRejected(ValueError):
    """A READ-only diagnostic plan cannot be safely preflighted."""


@dataclass(frozen=True, slots=True)
class DisconnectedReadPreflight:
    topology_digest: str
    status_digest: str
    registry_revision: str
    grant_fingerprint: str
    ready_step_ids: tuple[str, ...]
    ready_bound_ids: tuple[str, ...]
    fingerprint: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def external_result_verified(self) -> bool:
        return False

    @property
    def authenticated_clock_or_consent(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT_TYPE = DisconnectedReadPreflight


def _digest(payload: object) -> str:
    data = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(b"ARK-disconnected-registered-read-preflight-v1\0" + data).hexdigest()


def preview_registered_read_plan(
    plan: PlanGraph,
    registry: ToolRegistry,
    gate: PermissionGate,
    grants: tuple[CapabilityGrant, ...],
    *,
    observed_at_ms: int,
) -> DisconnectedReadPreflight:
    """Review exact ready READ steps without executing ANY registered backend.

    All steps, including not-ready descendants, must be registered as READ.
    The opt-in PermissionGate review checks exact grants only for ready steps.
    This deliberately cannot handle WRITE, token consumption, scheduling or
    external execution, even with synthetically valid grants.
    """
    if (
        type(plan) is not PlanGraph
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
    ):
        raise DisconnectedReadPreflightRejected("exact Planner/Registry/Gate required")
    if type(observed_at_ms) is not int or not 0 <= observed_at_ms <= _MAX_MS:
        raise DisconnectedReadPreflightRejected("invalid caller-observed clock value")
    if type(grants) is not tuple or len(grants) > _MAX_GRANTS:
        raise DisconnectedReadPreflightRejected("grants require bounded exact tuple")
    if any(type(item) is not CapabilityGrant for item in grants):
        raise DisconnectedReadPreflightRejected("grants require exact CapabilityGrant")
    if not 1 <= len(plan.steps) <= _MAX_STEPS:
        raise DisconnectedReadPreflightRejected("plan exceeds disconnected preflight budget")

    # Hold original carriers, not merely equal-valued mutable dataclass fields.
    grant_epoch = tuple(
        (grant, grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    )
    original_grants = grants
    try:
        topology = plan.topology_digest()
        status = plan.status_digest()
        revision = registry.revision
    except (TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedReadPreflightRejected("unstable plan or registry") from exc

    def stable() -> None:
        try:
            if grants is not original_grants or any(
                type(item) is not CapabilityGrant
                or item is not carrier
                or item.capability is not capability
                or item.scope is not scope
                or item.expires_at_ms is not expiry
                for item, (carrier, capability, scope, expiry) in zip(
                    grants, grant_epoch, strict=True,
                )
            ):
                raise DisconnectedReadPreflightRejected("grant carrier drift")
            if (
                plan.topology_digest() != topology
                or plan.status_digest() != status
                or registry.revision != revision
            ):
                raise DisconnectedReadPreflightRejected("plan or registry changed during review")
        except (TypeError, ValueError, PlanConflictError) as exc:
            if type(exc) is DisconnectedReadPreflightRejected:
                raise
            raise DisconnectedReadPreflightRejected("unstable preflight epoch") from exc

    stable()
    # Bind all graph actions before reviewing any grants: a non-ready WRITE
    # descendant must not silently slip through a READ-only preview.
    bindings: dict[str, BoundAction] = {}
    for step_id in sorted(plan.steps):
        stable()
        step = plan.steps[step_id]
        try:
            bound = registry.bind(step.call)
        except (KeyError, TypeError, ValueError) as exc:
            raise DisconnectedReadPreflightRejected("unregistered or changed tool") from exc
        stable()
        if (
            type(bound) is not BoundAction
            or bound.call is not step.call
            or bound.registry_revision != revision
            or type(bound.registration.effect) is not Effect
            or bound.registration.effect is not Effect.READ
        ):
            raise DisconnectedReadPreflightRejected("non-READ or unstable tool identity")
        bindings[step_id] = bound

    # A ready_steps() result is an independent callback boundary. Recompute
    # expected readiness from the authoritative detached statuses and exact
    # registered PlanStep carriers, rather than trusting an overridden method
    # that could omit, duplicate or introduce a not-yet-ready READ step.
    try:
        statuses = plan.statuses()
        expected_ready = tuple(
            plan.steps[step_id]
            for step_id in sorted(plan.steps)
            if statuses[step_id].state is StepState.PENDING
            and all(
                statuses[dep].state is StepState.SUCCEEDED
                for dep in plan.steps[step_id].depends_on
            )
        )
        ready = plan.ready_steps()
    except (KeyError, TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedReadPreflightRejected("unstable ready-step selection") from exc
    stable()
    if (
        type(ready) is not tuple
        or len(ready) != len(expected_ready)
        or any(
            actual is not expected
            for actual, expected in zip(ready, expected_ready, strict=True)
        )
    ):
        raise DisconnectedReadPreflightRejected("ready-step selection changed")
    ready_step_ids: list[str] = []
    ready_bound_ids: list[str] = []
    for step in ready:
        stable()
        bound = bindings[step.step_id]
        try:
            verified = gate.authorize_registered(
                registry, step.call, grants, now_ms=observed_at_ms,
            )
        except (KeyError, TypeError, ValueError, PermissionDenied) as exc:
            raise DisconnectedReadPreflightRejected("READ grant preflight denied") from exc
        stable()
        if (
            type(verified) is not BoundAction
            or verified.call is not step.call
            or verified.registration is not bound.registration
            or verified.registry_revision != revision
            or verified.bound_action_id != bound.bound_action_id
        ):
            raise DisconnectedReadPreflightRejected("READ binding changed during grants")
        ready_step_ids.append(step.step_id)
        ready_bound_ids.append(bound.bound_action_id)

    stable()
    grant_fingerprint = _digest([
        (grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    ])
    stable()
    entries = tuple(ready_step_ids)
    bound_ids = tuple(ready_bound_ids)
    fingerprint = _digest({
        "topology": topology,
        "status": status,
        "registry": revision,
        "grants": grant_fingerprint,
        "clock_observation_ms": observed_at_ms,
        "ready": list(zip(entries, bound_ids, strict=True)),
    })
    stable()
    result = DisconnectedReadPreflight(
        topology, status, revision, grant_fingerprint, entries, bound_ids, fingerprint,
    )
    stable()
    if (
        type(result) is not _RESULT_TYPE
        or result.topology_digest is not topology
        or result.status_digest is not status
        or result.registry_revision is not revision
        or result.grant_fingerprint is not grant_fingerprint
        or result.ready_step_ids is not entries
        or result.ready_bound_ids is not bound_ids
        or result.fingerprint is not fingerprint
    ):
        raise DisconnectedReadPreflightRejected("detached preflight result changed")
    return result
