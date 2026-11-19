"""Read-only preflight binding Planner DAG steps to one immutable ToolRegistry.

This module checks that every exact PlanStep ToolCall resolves to the same
registry revision. It does not authorize, schedule, dispatch, execute or retry
any tool. Digests are local consistency witnesses, not authenticated consent
or independent provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import Effect, PlanStep, ToolCall
from .planner import PlanGraph
from .registry import BoundAction, ToolRegistration, ToolRegistry

_DOMAIN = b"ARK-plan-registry-preflight-v1\0"
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps

_PLAN_METHODS = (
    "__init__", "_assert_plan_epoch", "_assert_status_epoch",
    "topology_digest", "status_digest", "statuses", "ready_steps",
)
_ORIGINAL_PLAN_METHODS = tuple(
    vars(PlanGraph).get(name) for name in _PLAN_METHODS
)
_REGISTRY_METHODS = (
    "bind", "resolve", "get", "revision", "_assert_registration_epoch",
)
_ORIGINAL_REGISTRY_METHODS = tuple(
    vars(ToolRegistry).get(name) for name in _REGISTRY_METHODS
)
_REGISTRATION_FIELDS = ("name", "capability", "effect", "backend_id", "backend")
_ORIGINAL_REGISTRATION_FIELDS = tuple(
    vars(ToolRegistration).get(name) for name in _REGISTRATION_FIELDS
)
_BOUND_FIELDS = ("registry_revision", "call", "registration", "bound_action_id")
_ORIGINAL_BOUND_FIELDS = tuple(
    vars(BoundAction).get(name) for name in _BOUND_FIELDS
)
_PLAN_FIELDS = ("step_id", "call", "depends_on")
_ORIGINAL_PLAN_FIELDS = tuple(vars(PlanStep).get(name) for name in _PLAN_FIELDS)
_CALL_FIELDS = ("tool", "capability", "scope", "arguments")
_ORIGINAL_CALL_FIELDS = tuple(vars(ToolCall).get(name) for name in _CALL_FIELDS)

_ORIGINAL_PLAN_TOPOLOGY = vars(PlanGraph)["topology_digest"]
_ORIGINAL_PLAN_STATUS = vars(PlanGraph)["status_digest"]
_ORIGINAL_PLAN_READY = vars(PlanGraph)["ready_steps"]
_ORIGINAL_PLAN_ASSERT = vars(PlanGraph)["_assert_plan_epoch"]
_ORIGINAL_STATUS_ASSERT = vars(PlanGraph)["_assert_status_epoch"]
_ORIGINAL_REGISTRY_BIND = vars(ToolRegistry)["bind"]
_ORIGINAL_REGISTRY_ASSERT = vars(ToolRegistry)["_assert_registration_epoch"]


class PlanRegistryPreflightRejected(RuntimeError):
    """A plan or registry could not be bound to one stable local epoch."""


@dataclass(frozen=True, slots=True)
class PlanRegistryBinding:
    step_id: str
    tool_name: str
    capability: str
    effect: Effect
    backend_id: str
    request_id: str
    bound_action_id: str

    @property
    def permission_granted(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlanRegistryPreflight:
    plan_topology_digest: str
    plan_status_digest: str
    registry_revision: str
    ready_step_ids: tuple[str, ...]
    bindings: tuple[PlanRegistryBinding, ...]
    fingerprint: str

    @property
    def permission_granted(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


_RESULT_TYPE = PlanRegistryPreflight
_BINDING_TYPE = PlanRegistryBinding
_RESULT_FIELDS = (
    "plan_topology_digest", "plan_status_digest", "registry_revision",
    "ready_step_ids", "bindings", "fingerprint",
)
_BINDING_RESULT_FIELDS = (
    "step_id", "tool_name", "capability", "effect",
    "backend_id", "request_id", "bound_action_id",
)
_RESULT_DENIALS = (
    "permission_granted", "dispatch_authorized", "tool_execution_authorized",
    "automatic_replay_authorized", "trusted_clock_verified", "consent_verified",
)
_BINDING_DENIALS = (
    "permission_granted", "dispatch_authorized", "tool_execution_authorized",
)
_ORIGINAL_RESULT_INIT = vars(_RESULT_TYPE)["__init__"]
_ORIGINAL_BINDING_INIT = vars(_BINDING_TYPE)["__init__"]
_ORIGINAL_RESULT_MEMBERS = tuple(
    vars(_RESULT_TYPE).get(name)
    for name in (*_RESULT_FIELDS, *_RESULT_DENIALS, "__new__", "__getattribute__", "__getattr__")
)
_ORIGINAL_BINDING_MEMBERS = tuple(
    vars(_BINDING_TYPE).get(name)
    for name in (
        *_BINDING_RESULT_FIELDS, *_BINDING_DENIALS,
        "__new__", "__getattribute__", "__getattr__",
    )
)


def _require_original_protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or PlanGraph is not type.__getattribute__(PlanGraph, "__class__") and False
    ):
        raise PlanRegistryPreflightRejected("plan preflight digest protocol changed")
    if (
        any(
            vars(PlanGraph).get(name) is not original
            for name, original in zip(_PLAN_METHODS, _ORIGINAL_PLAN_METHODS, strict=True)
        )
        or any(
            vars(ToolRegistry).get(name) is not original
            for name, original in zip(
                _REGISTRY_METHODS, _ORIGINAL_REGISTRY_METHODS, strict=True,
            )
        )
        or any(
            vars(ToolRegistration).get(name) is not original
            for name, original in zip(
                _REGISTRATION_FIELDS, _ORIGINAL_REGISTRATION_FIELDS, strict=True,
            )
        )
        or any(
            vars(BoundAction).get(name) is not original
            for name, original in zip(_BOUND_FIELDS, _ORIGINAL_BOUND_FIELDS, strict=True)
        )
        or any(
            vars(PlanStep).get(name) is not original
            for name, original in zip(_PLAN_FIELDS, _ORIGINAL_PLAN_FIELDS, strict=True)
        )
        or any(
            vars(ToolCall).get(name) is not original
            for name, original in zip(_CALL_FIELDS, _ORIGINAL_CALL_FIELDS, strict=True)
        )
        or PlanRegistryPreflight is not _RESULT_TYPE
        or PlanRegistryBinding is not _BINDING_TYPE
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or vars(_BINDING_TYPE).get("__init__") is not _ORIGINAL_BINDING_INIT
        or tuple(
            vars(_RESULT_TYPE).get(name)
            for name in (
                *_RESULT_FIELDS, *_RESULT_DENIALS,
                "__new__", "__getattribute__", "__getattr__",
            )
        ) != _ORIGINAL_RESULT_MEMBERS
        or tuple(
            vars(_BINDING_TYPE).get(name)
            for name in (
                *_BINDING_RESULT_FIELDS, *_BINDING_DENIALS,
                "__new__", "__getattribute__", "__getattr__",
            )
        ) != _ORIGINAL_BINDING_MEMBERS
    ):
        raise PlanRegistryPreflightRejected("plan or registry contract changed")


def _require_instances(graph: PlanGraph, registry: ToolRegistry) -> None:
    _require_original_protocol()
    if type(graph) is not PlanGraph or type(registry) is not ToolRegistry:
        raise PlanRegistryPreflightRejected("exact PlanGraph and ToolRegistry required")
    if any(name in vars(graph) for name in _PLAN_METHODS):
        raise PlanRegistryPreflightRejected("PlanGraph method shadowing rejected")
    if any(name in vars(registry) for name in _REGISTRY_METHODS):
        raise PlanRegistryPreflightRejected("ToolRegistry method shadowing rejected")


def review_plan_registry_preflight(
    graph: PlanGraph,
    registry: ToolRegistry,
) -> PlanRegistryPreflight:
    """Bind every plan step to one immutable registry snapshot without dispatch."""
    _require_instances(graph, registry)
    try:
        _ORIGINAL_PLAN_ASSERT(graph)
        _ORIGINAL_STATUS_ASSERT(graph)
        steps_mapping = graph.steps
        if type(steps_mapping) is not MappingProxyType:
            raise PlanRegistryPreflightRejected("PlanGraph step mapping changed")
        steps_epoch = tuple(
            (
                step_id, step, step.step_id, step.call, step.depends_on,
                step.call.tool, step.call.capability, step.call.scope,
                step.call.arguments, step.call.request_id,
            )
            for step_id, step in sorted(steps_mapping.items())
        )
        status_epoch = graph._status_epoch
        topology_digest = _ORIGINAL_PLAN_TOPOLOGY(graph)
        status_digest = _ORIGINAL_PLAN_STATUS(graph)
        ready = _ORIGINAL_PLAN_READY(graph)
        ready_ids = tuple(step.step_id for step in ready)
        registry_revision = registry.revision
        _ORIGINAL_REGISTRY_ASSERT(registry)
    except Exception as exc:
        if isinstance(exc, PlanRegistryPreflightRejected):
            raise
        raise PlanRegistryPreflightRejected(
            "plan or registry snapshot could not be captured"
        ) from exc

    bindings: list[PlanRegistryBinding] = []
    for step_id, step, *_ in steps_epoch:
        _require_instances(graph, registry)
        try:
            bound = _ORIGINAL_REGISTRY_BIND(registry, step.call)
        except Exception as exc:
            raise PlanRegistryPreflightRejected(
                "plan step has no stable registry binding"
            ) from exc
        _require_instances(graph, registry)
        try:
            if (
                type(bound) is not BoundAction
                or bound.call is not step.call
                or bound.registry_revision is not registry_revision
                or type(bound.registration) is not ToolRegistration
            ):
                raise PlanRegistryPreflightRejected("bound action carrier changed")
            registration = bound.registration
            if (
                registration.name != step.call.tool
                or registration.capability != step.call.capability
                or type(registration.effect) is not Effect
                or type(registration.backend_id) is not str
                or not registration.backend_id
                or type(bound.bound_action_id) is not str
                or not bound.bound_action_id
                or type(step.step_id) is not str
                or type(step.call.request_id) is not str
            ):
                raise PlanRegistryPreflightRejected(
                    "bound action identity does not match the plan step"
                )
            bindings.append(PlanRegistryBinding(
                step_id=step_id,
                tool_name=registration.name,
                capability=registration.capability,
                effect=registration.effect,
                backend_id=registration.backend_id,
                request_id=step.call.request_id,
                bound_action_id=bound.bound_action_id,
            ))
        except (AttributeError, TypeError, ValueError) as exc:
            if isinstance(exc, PlanRegistryPreflightRejected):
                raise
            raise PlanRegistryPreflightRejected(
                "bound action fields changed during preflight"
            ) from exc

    try:
        _ORIGINAL_PLAN_ASSERT(graph)
        _ORIGINAL_STATUS_ASSERT(graph)
        _ORIGINAL_REGISTRY_ASSERT(registry)
        if (
            graph.steps is not steps_mapping
            or graph._status_epoch is not status_epoch
            or registry.revision is not registry_revision
            or _ORIGINAL_PLAN_TOPOLOGY(graph) != topology_digest
            or _ORIGINAL_PLAN_STATUS(graph) != status_digest
            or tuple(step.step_id for step in _ORIGINAL_PLAN_READY(graph)) != ready_ids
            or tuple(
                (
                    step_id, step, step.step_id, step.call, step.depends_on,
                    step.call.tool, step.call.capability, step.call.scope,
                    step.call.arguments, step.call.request_id,
                )
                for step_id, step in sorted(graph.steps.items())
            ) != steps_epoch
        ):
            raise PlanRegistryPreflightRejected(
                "plan status, topology or registry changed during preflight"
            )
    except Exception as exc:
        if isinstance(exc, PlanRegistryPreflightRejected):
            raise
        raise PlanRegistryPreflightRejected(
            "plan or registry changed during final verification"
        ) from exc

    binding_rows = tuple(
        (
            item.step_id, item.tool_name, item.capability, item.effect.value,
            item.backend_id, item.request_id, item.bound_action_id,
        )
        for item in bindings
    )
    payload = json.dumps(
        (
            topology_digest, status_digest, registry_revision,
            ready_ids, binding_rows,
        ),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    _require_original_protocol()
    fingerprint = hashlib.sha256(_DOMAIN + payload).hexdigest()
    _require_original_protocol()
    return PlanRegistryPreflight(
        plan_topology_digest=topology_digest,
        plan_status_digest=status_digest,
        registry_revision=registry_revision,
        ready_step_ids=ready_ids,
        bindings=tuple(bindings),
        fingerprint=fingerprint,
    )


__all__ = [
    "PlanRegistryBinding",
    "PlanRegistryPreflight",
    "PlanRegistryPreflightRejected",
    "review_plan_registry_preflight",
]
