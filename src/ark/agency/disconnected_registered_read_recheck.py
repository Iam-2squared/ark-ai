"""Restart/review-only revalidation of a registry-bound READ preflight receipt.

A prior detached diagnostic can be stale even when its request and registry
strings still look correct. Re-run the immutable ToolRegistry and exact-scope
PermissionGate checks against the original caller inputs. No backend is
supplied, no external READ is dispatched, and the result grants no authority.
This is deliberately not a trusted clock or durable grant verifier.
"""

from __future__ import annotations

from .contracts import CapabilityGrant, ToolCall
from .disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    DisconnectedReadPreflightRejected,
    review_disconnected_registered_read,
)
from .policy import PermissionGate
from .registry import ToolRegistry

_RECEIPT = DisconnectedReadPreflight
_FLAGS = (
    "backend_dispatched",
    "external_read_authorized",
    "write_authorized",
    "trusted_clock_verified",
    "durable_permission_proven",
)


class DisconnectedReadReceiptRejected(ValueError):
    """A locally retained READ diagnostic cannot be re-established."""


def verify_disconnected_registered_read_receipt(
    receipt: DisconnectedReadPreflight,
    registry: ToolRegistry,
    gate: PermissionGate,
    call: ToolCall,
    grants: tuple[CapabilityGrant, ...],
    *,
    now_ms: int,
) -> None:
    """Rebind one retained synthetic READ receipt without any ToolBackend call.

    A valid receipt is not permission to read data. Rechecking after restart
    requires reconstructing the same registry, call, grant and synthetic time
    inputs. It cannot authenticate their origin or turn a caller-held receipt
    into an independently retained approval.
    """
    if (
        type(receipt) is not _RECEIPT
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(call) is not ToolCall
        or type(grants) is not tuple
        or len(grants) > 128
        or any(type(grant) is not CapabilityGrant for grant in grants)
        or type(now_ms) is not int
        or not 0 <= now_ms <= (1 << 63) - 1
    ):
        raise DisconnectedReadReceiptRejected("exact bounded READ receipt inputs required")

    receipt_epoch = (
        receipt.registry_revision,
        receipt.bound_action_id,
        receipt.request_id,
        receipt.tool_name,
        receipt.capability,
    )
    call_epoch = (call.tool, call.capability, call.scope, call.arguments)
    denial_descriptors = tuple(getattr(_RECEIPT, flag) for flag in _FLAGS)
    request_id = call.request_id  # computed: compare VALUE, not string identity
    grant_epochs = tuple(
        (grant, grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    )
    try:
        revision = registry.revision
    except (TypeError, ValueError) as exc:
        raise DisconnectedReadReceiptRejected("invalid registry epoch") from exc

    def stable() -> None:
        try:
            if (
                type(receipt) is not _RECEIPT
                or any(
                    current is not initial
                    for current, initial in zip(
                        (
                            receipt.registry_revision, receipt.bound_action_id,
                            receipt.request_id, receipt.tool_name, receipt.capability,
                        ),
                        receipt_epoch, strict=True,
                    )
                )
                or type(call) is not ToolCall
                or any(
                    current is not initial
                    for current, initial in zip(
                        (call.tool, call.capability, call.scope, call.arguments),
                        call_epoch, strict=True,
                    )
                )
                or call.request_id != request_id
                or len(grants) != len(grant_epochs)
                or any(
                    type(grant) is not CapabilityGrant
                    or grant is not original
                    or grant.capability is not capability
                    or grant.scope is not scope
                    or grant.expires_at_ms is not expiry
                    for grant, (original, capability, scope, expiry) in zip(
                        grants, grant_epochs, strict=True,
                    )
                )
                or registry.revision != revision
                or any(
                    getattr(_RECEIPT, flag) is not original
                    for flag, original in zip(
                        _FLAGS, denial_descriptors, strict=True,
                    )
                )
                or any(getattr(receipt, flag) is not False for flag in _FLAGS)
            ):
                raise DisconnectedReadReceiptRejected("READ receipt or input epoch changed")
            # The last authority getter is itself a callback. No input
            # carrier may change while returning the exact False value.
            if (
                any(current is not initial for current, initial in zip(
                    (
                        receipt.registry_revision, receipt.bound_action_id,
                        receipt.request_id, receipt.tool_name, receipt.capability,
                    ), receipt_epoch, strict=True,
                ))
                or any(current is not initial for current, initial in zip(
                    (call.tool, call.capability, call.scope, call.arguments),
                    call_epoch, strict=True,
                ))
                or call.request_id != request_id
                or any(
                    grant is not original
                    or grant.capability is not capability
                    or grant.scope is not scope
                    or grant.expires_at_ms is not expiry
                    for grant, (original, capability, scope, expiry) in zip(
                        grants, grant_epochs, strict=True,
                    )
                )
                or registry.revision != revision
                or any(
                    getattr(_RECEIPT, flag) is not original
                    for flag, original in zip(
                        _FLAGS, denial_descriptors, strict=True,
                    )
                )
            ):
                raise DisconnectedReadReceiptRejected("READ receipt or input epoch changed")
        except DisconnectedReadReceiptRejected:
            raise
        except (AttributeError, TypeError, ValueError) as exc:
            raise DisconnectedReadReceiptRejected("READ receipt epoch is invalid") from exc

    stable()
    try:
        expected = review_disconnected_registered_read(
            registry, gate, call, grants, now_ms=now_ms,
        )
    except (DisconnectedReadPreflightRejected, KeyError, TypeError, ValueError) as exc:
        raise DisconnectedReadReceiptRejected("fresh registry READ review denied") from exc
    stable()
    if type(expected) is not _RECEIPT or any(
        type(field) is not str for field in receipt_epoch
    ):
        raise DisconnectedReadReceiptRejected("retained READ binding differs")
    expected_epoch = (
        expected.registry_revision, expected.bound_action_id,
        expected.request_id, expected.tool_name, expected.capability,
    )

    def expected_stable() -> None:
        fields = (
            expected.registry_revision, expected.bound_action_id,
            expected.request_id, expected.tool_name, expected.capability,
        )
        if (
            type(expected) is not _RECEIPT
            or fields != receipt_epoch
            or any(current is not initial for current, initial in zip(
                fields, expected_epoch, strict=True,
            ))
            or any(getattr(expected, flag) is not False for flag in _FLAGS)
            or any(
                getattr(_RECEIPT, flag) is not original
                for flag, original in zip(
                    _FLAGS, denial_descriptors, strict=True,
                )
            )
            # Re-read after the LAST descriptor: a getter may have altered
            # the previously examined ID but returned the exact False.
            or any(current is not initial for current, initial in zip(
                (
                    expected.registry_revision, expected.bound_action_id,
                    expected.request_id, expected.tool_name, expected.capability,
                ), expected_epoch, strict=True,
            ))
            or any(
                getattr(_RECEIPT, flag) is not original
                for flag, original in zip(
                    _FLAGS, denial_descriptors, strict=True,
                )
            )
        ):
            raise DisconnectedReadReceiptRejected("retained READ binding differs")

    expected_stable()
    stable()
    expected_stable()
    # No execution token, receipt, or dispatch hook is returned.
    return None
