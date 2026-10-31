"""Registry-bound, deliberately non-executing READ preflight.

This bridge checks the real immutable ToolRegistry and exact-scope PermissionGate
without installing a ToolBackend executor. It refuses every WRITE, even if a
caller supplies a one-shot token elsewhere. Its result is not permission to
perform an external READ, nor a trusted-clock or durable authorization proof.
"""

from __future__ import annotations

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
            ) is False
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
        before = registry.bind(call)
        stable_inputs()
        if (
            type(before) is not BoundAction
            or before.registration.effect is not Effect.READ
            or before.registration.name is not call_epoch[0]
            or before.registration.capability is not call_epoch[1]
        ):
            raise DisconnectedReadPreflightRejected("non-READ registration is forbidden")
        verified = gate.authorize_registered(
            registry, call, grants, now_ms=now_ms,
        )
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

    report = _REPORT(
        before.registry_revision, before.bound_action_id, request_id,
        before.registration.name, before.registration.capability,
    )
    stable_inputs()
    if (
        type(report) is not _REPORT
        or report.registry_revision is not before.registry_revision
        or report.bound_action_id is not before.bound_action_id
        or report.request_id is not request_id
        or report.tool_name is not before.registration.name
        or report.capability is not before.registration.capability
        or report.backend_dispatched is not False
        or report.external_read_authorized is not False
        or report.write_authorized is not False
        or report.trusted_clock_verified is not False
        or report.durable_permission_proven is not False
    ):
        raise DisconnectedReadPreflightRejected("preflight report gained authority")
    stable_inputs()
    return report
