"""Registry-bound, deliberately non-executing READ preflight.

This bridge checks the real immutable ToolRegistry and exact-scope PermissionGate
without installing a ToolBackend executor. It refuses every WRITE, even if a
caller supplies a one-shot token elsewhere. Its result is not permission to
perform an external READ, nor a trusted-clock or durable authorization proof.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

from .contracts import CapabilityGrant, Effect, PermissionDenied, ToolCall
from .policy import PermissionGate
from .registry import BoundAction, ToolRegistry

_MAX_GRANTS = 128


class DisconnectedReadPreflightRejected(ValueError):
    """No trustworthy, strictly disconnected READ-only review is available."""


@dataclass(frozen=True, slots=True)
class DisconnectedReadPreflight:
    registry_revision: str
    bound_action_id: str
    request_id: str
    tool_name: str
    capability: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def external_read_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def durable_permission_proven(self) -> bool:
        return False


_REPORT = DisconnectedReadPreflight
_REPORT_DENIALS = (
    "backend_dispatched", "external_read_authorized", "write_authorized",
    "trusted_clock_verified", "durable_permission_proven",
)
_ORIGINAL_REPORT_DENIALS = tuple(
    vars(_REPORT)[name] for name in _REPORT_DENIALS
)
# Even an inert READ preflight report is executable Python during construction
# and attribute access. Pin field slots, constructor and inherited lookup
# hooks before touching the registry or invoking the result constructor.
_REPORT_FIELDS = (
    "registry_revision", "bound_action_id", "request_id",
    "tool_name", "capability",
)
_REPORT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT)[name] for name in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT).get(name) for name in _REPORT_HOOKS)
_ORIGINAL_REGISTERED_POLICY = vars(PermissionGate)["authorize_registered"]


def _assert_original_report_denials() -> None:
    if (
        DisconnectedReadPreflight is not _REPORT
        or any(
            vars(_REPORT).get(name) is not original
            for names, originals in (
                (_REPORT_DENIALS, _ORIGINAL_REPORT_DENIALS),
                (_REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS),
                (_REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise DisconnectedReadPreflightRejected(
            "preflight report authority definition changed"
        )


def review_disconnected_registered_read(
    registry: ToolRegistry,
    gate: PermissionGate,
    call: ToolCall,
    grants: tuple[CapabilityGrant, ...],
    *,
    now_ms: int,
) -> DisconnectedReadPreflight:
    """Bind and inspect an exact READ without touching the registered backend.

    The caller supplies a synthetic time; the function does not read a clock,
    consume a one-shot token, persist approval, or call a backend. This
    deliberately rejects all WRITE registrations *before* PermissionGate.
    """
    _assert_original_report_denials()

    def stable_gate_method() -> None:
        # A class-level or instance-level replacement can forge a value-equal
        # BoundAction without evaluating grants. Do not mistake such a return
        # value for a PermissionGate decision, even in disconnected diagnostics.
        if (
            vars(PermissionGate).get("authorize_registered")
            is not _ORIGINAL_REGISTERED_POLICY
            or inspect.getattr_static(gate, "authorize_registered")
            is not _ORIGINAL_REGISTERED_POLICY
        ):
            raise DisconnectedReadPreflightRejected(
                "registered READ policy implementation changed"
            )

    if (
        type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(call) is not ToolCall
        or type(grants) is not tuple
        or len(grants) > _MAX_GRANTS
        or any(type(grant) is not CapabilityGrant for grant in grants)
        or type(now_ms) is not int
        or not 0 <= now_ms <= (1 << 63) - 1
    ):
        raise DisconnectedReadPreflightRejected("exact bounded preflight inputs required")
    stable_gate_method()

    call_epoch = (call.tool, call.capability, call.scope, call.arguments)
    grant_epochs = tuple(
        (grant, grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    )
    request_id = call.request_id

    def stable_inputs() -> None:
        if (
            (call.tool, call.capability, call.scope, call.request_id)
            != (*call_epoch[:3], request_id)
            or not all(
                current is original
                for current, original in zip(
                    (call.tool, call.capability, call.scope, call.arguments),
                    call_epoch, strict=True,
                )
            )
            or any(
                type(grant) is not CapabilityGrant
                or grant.capability is not capability
                or grant.scope is not scope
                or grant.expires_at_ms is not expires
                for grant, capability, scope, expires in grant_epochs
            )
        ):
            raise DisconnectedReadPreflightRejected("preflight input identity changed")

    stable_inputs()
    try:
        stable_gate_method()
        before = registry.bind(call)
        stable_gate_method()
        stable_inputs()
        if (
            type(before) is not BoundAction
            or before.registration.effect is not Effect.READ
            or before.registration.name is not call_epoch[0]
            or before.registration.capability is not call_epoch[1]
        ):
            raise DisconnectedReadPreflightRejected("non-READ registration is forbidden")
        stable_gate_method()
        verified = gate.authorize_registered(
            registry, call, grants, now_ms=now_ms,
        )
        stable_gate_method()
        stable_inputs()
        if (
            type(verified) is not BoundAction
            or verified.registration is not before.registration
            or verified.registry_revision != before.registry_revision
            or verified.bound_action_id != before.bound_action_id
            or verified.call is not call
            or registry.revision != before.registry_revision
            or verified.registration.effect is not Effect.READ
        ):
            raise DisconnectedReadPreflightRejected("registered READ binding changed")
        stable_inputs()
    except DisconnectedReadPreflightRejected:
        raise
    except (KeyError, PermissionDenied, TypeError, ValueError) as exc:
        raise DisconnectedReadPreflightRejected("registered READ preflight denied") from exc

    report_epoch = (
        before.registry_revision, before.bound_action_id, request_id,
        before.registration.name, before.registration.capability,
    )
    _assert_original_report_denials()
    report = _REPORT(*report_epoch)

    def stable_report() -> None:
        # A false-looking getter may change a frozen report, or install a new
        # getter for a later denial flag. Refuse both within the same review.
        _assert_original_report_denials()
        if type(report) is not _REPORT:
            raise DisconnectedReadPreflightRejected("preflight report gained authority")

        def same_fields() -> bool:
            return all(
                value is initial for value, initial in zip(
                    (
                        report.registry_revision, report.bound_action_id,
                        report.request_id, report.tool_name, report.capability,
                    ), report_epoch, strict=True,
                )
            )

        if not same_fields():
            raise DisconnectedReadPreflightRejected("preflight report gained authority")
        for flag in _REPORT_DENIALS:
            _assert_original_report_denials()
            if getattr(report, flag) is not False:
                raise DisconnectedReadPreflightRejected(
                    "preflight report gained authority"
                )
            _assert_original_report_denials()
            if not same_fields():
                raise DisconnectedReadPreflightRejected(
                    "preflight report changed during denial check"
                )

    stable_inputs()
    stable_gate_method()
    stable_report()
    stable_inputs()
    stable_gate_method()
    stable_report()
    return report
