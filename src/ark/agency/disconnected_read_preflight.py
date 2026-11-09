"""Fail-closed, disconnected Planner/Registry/PermissionGate READ preflight.

This joins already-tested local contracts without calling a backend. An observed
clock value and caller-provided grants have no independent authenticity. The
content-free result never confers permission to dispatch a real action.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass

from .contracts import CapabilityGrant, Effect, PermissionDenied, PlanConflictError, StepState
from .planner import PlanGraph
from .policy import PermissionGate
from .registry import BoundAction, ToolRegistry

_MAX_STEPS = 24
_MAX_GRANTS = 128
_MAX_MS = 2**63 - 1
_DOMAIN = b"ARK-disconnected-registered-read-preflight-v1\0"
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_BUDGETS = (_MAX_STEPS, _MAX_GRANTS, _MAX_MS)


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
_ORIGINAL_RESULT_INIT = vars(_RESULT_TYPE)["__init__"]
_RESULT_DENIALS = (
    "dispatch_authorized", "external_result_verified",
    "authenticated_clock_or_consent", "automatic_replay_authorized",
)
_ORIGINAL_RESULT_DENIALS = tuple(
    vars(_RESULT_TYPE)[name] for name in _RESULT_DENIALS
)
_ORIGINAL_REGISTERED_GATE = vars(PermissionGate)["authorize_registered"]
_RESULT_FIELDS = (
    "topology_digest", "status_digest", "registry_revision",
    "grant_fingerprint", "ready_step_ids", "ready_bound_ids", "fingerprint",
)
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_CARRIERS = tuple(
    vars(_RESULT_TYPE).get(key) for key in _RESULT_FIELDS + _RESULT_HOOKS
)


def _assert_original_digest_pipeline() -> None:
    """Reject substituted codec/digest authority before private plan or grants.

    Python module-identity checks are local fault-injection guards, not
    authenticated provenance or permission to execute a registered backend.
    """
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or (_MAX_STEPS, _MAX_GRANTS, _MAX_MS) != _ORIGINAL_BUDGETS
    ):
        raise DisconnectedReadPreflightRejected(
            "READ preflight digest dependencies changed"
        )


def _assert_original_result_denials() -> None:
    # Even an equally False-looking replacement is not an authority witness.
    if (
        DisconnectedReadPreflight is not _RESULT_TYPE
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT_TYPE).get(name) is not expected
            for name, expected in zip(
                _RESULT_FIELDS + _RESULT_HOOKS,
                _ORIGINAL_RESULT_CARRIERS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_DENIALS, _ORIGINAL_RESULT_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedReadPreflightRejected(
            "READ plan preflight authority descriptor changed"
        )


def _assert_original_gate(gate: PermissionGate) -> None:
    # A fake registry-bound decision may be value-equal to the real one.
    # Inspect statically so a hostile descriptor is never invoked by the check.
    if (
        vars(PermissionGate).get("authorize_registered")
        is not _ORIGINAL_REGISTERED_GATE
        or inspect.getattr_static(gate, "authorize_registered")
        is not _ORIGINAL_REGISTERED_GATE
    ):
        raise DisconnectedReadPreflightRejected(
            "registered READ gate implementation changed"
        )


def _digest(payload: object) -> str:
    _assert_original_digest_pipeline()
    data = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    _assert_original_digest_pipeline()
    result = hashlib.sha256(_DOMAIN + data).hexdigest()
    _assert_original_digest_pipeline()
    return result


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
    _assert_original_digest_pipeline()
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
    _assert_original_result_denials()
    _assert_original_digest_pipeline()
    # Validate the real registered permission method BEFORE any registry or
    # planner callback. A counterfeit method must never be executed first.
    _assert_original_gate(gate)

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
        _assert_original_digest_pipeline()
        _assert_original_gate(gate)
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
        # A digest/revision callback can replace the policy method. Validate
        # again before the next gate call; no fabricated grant may run.
        _assert_original_gate(gate)

    stable()
    # Bind all graph actions before reviewing any grants: a non-ready WRITE
    # descendant must not silently slip through a READ-only preview.
    bindings: dict[str, BoundAction] = {}
    # Registry.bind() returns a frozen *carrier*, not an immutable receipt.
    # A later gate callback must not replace an earlier bound ID, registration,
    # or call with an equal-valued object after that binding was checked.
    bound_epochs: list[tuple[str, BoundAction, object, object, object, object]] = []

    def assert_bound_epochs() -> None:
        if len(bindings) != len(bound_epochs):
            raise DisconnectedReadPreflightRejected("READ binding set changed")
        try:
            for key, original, call, registration, bound_revision, bound_id in bound_epochs:
                current = bindings.get(key)
                if (
                    current is not original
                    or type(current) is not BoundAction
                    or current.call is not call
                    or current.registration is not registration
                    or current.registry_revision is not bound_revision
                    or current.bound_action_id is not bound_id
                ):
                    raise DisconnectedReadPreflightRejected("READ binding carrier changed")
        except (AttributeError, TypeError, ValueError) as exc:
            if type(exc) is DisconnectedReadPreflightRejected:
                raise
            raise DisconnectedReadPreflightRejected("READ binding carrier invalid") from exc

    for step_id in sorted(plan.steps):
        stable()
        assert_bound_epochs()
        step = plan.steps[step_id]
        try:
            bound = registry.bind(step.call)
        except (KeyError, TypeError, ValueError) as exc:
            raise DisconnectedReadPreflightRejected("unregistered or changed tool") from exc
        stable()
        assert_bound_epochs()
        if (
            type(bound) is not BoundAction
            or bound.call is not step.call
            or bound.registry_revision != revision
            or type(bound.registration.effect) is not Effect
            or bound.registration.effect is not Effect.READ
        ):
            raise DisconnectedReadPreflightRejected("non-READ or unstable tool identity")
        bindings[step_id] = bound
        bound_epochs.append((
            step_id, bound, bound.call, bound.registration,
            bound.registry_revision, bound.bound_action_id,
        ))
        assert_bound_epochs()

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
    assert_bound_epochs()
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
        assert_bound_epochs()
        bound = bindings[step.step_id]
        _assert_original_gate(gate)
        try:
            verified = gate.authorize_registered(
                registry, step.call, grants, now_ms=observed_at_ms,
            )
        except (KeyError, TypeError, ValueError, PermissionDenied) as exc:
            raise DisconnectedReadPreflightRejected("READ grant preflight denied") from exc
        stable()
        assert_bound_epochs()
        # Reentrant legacy diagnostics may legitimately change the plan or
        # grant first; preserve their specific denial, then reject a forged
        # gate method even if it returned a value-equal registry binding.
        _assert_original_gate(gate)
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
    assert_bound_epochs()
    grant_fingerprint = _digest([
        (grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    ])
    stable()
    assert_bound_epochs()
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
    assert_bound_epochs()
    # The last digest/stability callbacks may replace this class initializer.
    # Reject before invoking a potentially hostile result constructor.
    _assert_original_result_denials()
    result = DisconnectedReadPreflight(
        topology, status, revision, grant_fingerprint, entries, bound_ids, fingerprint,
    )
    stable()
    assert_bound_epochs()
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
    assert_bound_epochs()

    def same_result() -> bool:
        return (
            type(result) is _RESULT_TYPE
            and result.topology_digest is topology
            and result.status_digest is status
            and result.registry_revision is revision
            and result.grant_fingerprint is grant_fingerprint
            and result.ready_step_ids is entries
            and result.ready_bound_ids is bound_ids
            and result.fingerprint is fingerprint
        )

    # Denial properties are callback surfaces; check original descriptors
    # and all result carriers again after EACH getter and at return.
    _assert_original_result_denials()
    for flag in _RESULT_DENIALS:
        _assert_original_result_denials()
        if getattr(result, flag) is not False:
            raise DisconnectedReadPreflightRejected(
                "READ plan preflight gained authority"
            )
        _assert_original_result_denials()
        stable()
        assert_bound_epochs()
        _assert_original_gate(gate)
        if not same_result():
            raise DisconnectedReadPreflightRejected(
                "READ plan preflight result changed during authority review"
            )
    _assert_original_result_denials()
    stable()
    assert_bound_epochs()
    _assert_original_gate(gate)
    if not same_result():
        raise DisconnectedReadPreflightRejected(
            "READ plan preflight result changed at return"
        )
    return result
