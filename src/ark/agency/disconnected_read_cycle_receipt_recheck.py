"""Re-derive a retained mock READ-cycle receipt without trusting its provenance.

This is an offline, no-backend verifier. A matching digest authenticates neither
the observer's clock nor grant provenance and NEVER authorizes dispatch/replay.
"""

from __future__ import annotations

import inspect

from .contracts import CapabilityGrant, PlanConflictError
from .disconnected_read_cycle import (
    DisconnectedReadCycleReceipt,
    DisconnectedReadCycleRejected,
    simulate_registered_read_cycle,
)
from .planner import PlanGraph
from .policy import PermissionGate
from .registry import ToolRegistry


class DisconnectedReadCycleReceiptRejected(ValueError):
    """A retained mock READ-cycle receipt is stale or inconsistent."""


_RECEIPT = DisconnectedReadCycleReceipt
_FLAGS = (
    "dispatch_authorized",
    "external_result_verified",
    "automatic_replay_authorized",
    "authenticated_clock_or_consent",
)
_ORIGINAL_DENIALS = tuple(vars(_RECEIPT)[name] for name in _FLAGS)


def _require_original_denials(value: DisconnectedReadCycleReceipt) -> None:
    # A local False-like replacement property is not the original inert
    # receipt contract. Inspect without invoking any untrusted getter.
    if (
        DisconnectedReadCycleReceipt is not _RECEIPT
        or type(value) is not _RECEIPT
        or any(
            vars(_RECEIPT).get(name) is not original
            or inspect.getattr_static(value, name, None) is not original
            for name, original in zip(_FLAGS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DisconnectedReadCycleReceiptRejected(
            "READ receipt or inputs changed: denial descriptor substituted"
        )


def _denials_still_false(value: DisconnectedReadCycleReceipt) -> bool:
    for name in _FLAGS:
        _require_original_denials(value)
        if getattr(value, name) is not False:
            return False
        _require_original_denials(value)
    return True


def verify_disconnected_read_cycle_receipt(
    receipt: DisconnectedReadCycleReceipt,
    plan: PlanGraph,
    registry: ToolRegistry,
    gate: PermissionGate,
    grants: tuple[CapabilityGrant, ...],
    *,
    observed_at_ms: int,
) -> None:
    """Re-simulate the original detached DAG; do not execute or return authority.

    Only a fresh PENDING plan may be supplied. Retained receipts are local
    diagnostics, not authorization credentials or cross-process attestation.
    """
    if (
        type(receipt) is not _RECEIPT
        or type(plan) is not PlanGraph
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(grants) is not tuple
        or len(grants) > 128
        or any(type(grant) is not CapabilityGrant for grant in grants)
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms <= 2**63 - 1
    ):
        raise DisconnectedReadCycleReceiptRejected("exact bounded receipt inputs required")

    _require_original_denials(receipt)
    original = (
        receipt.topology_digest, receipt.registry_revision,
        receipt.wave_bound_step_hashes, receipt.final_status_digest,
        receipt.fingerprint,
    )
    if (
        any(type(value) is not str for value in (
            original[0], original[1], original[3], original[4],
        ))
        or type(original[2]) is not tuple
        or any(
            type(wave) is not tuple
            or any(type(item) is not str for item in wave)
            for wave in original[2]
        )
    ):
        raise DisconnectedReadCycleReceiptRejected("retained receipt has invalid shape")

    try:
        topology = plan.topology_digest()
        status = plan.status_digest()
        revision = registry.revision
        grant_epoch = tuple(
            (grant, grant.capability, grant.scope, grant.expires_at_ms)
            for grant in grants
        )
    except (AttributeError, TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedReadCycleReceiptRejected("invalid original READ inputs") from exc

    def stable() -> None:
        _require_original_denials(receipt)
        try:
            fields = (
                receipt.topology_digest, receipt.registry_revision,
                receipt.wave_bound_step_hashes, receipt.final_status_digest,
                receipt.fingerprint,
            )
            if (
                type(receipt) is not _RECEIPT
                or any(value is not first for value, first in zip(
                    fields, original, strict=True,
                ))
                or plan.topology_digest() != topology
                or plan.status_digest() != status
                or registry.revision != revision
                or any(
                    type(grant) is not CapabilityGrant
                    or grant is not carrier
                    or grant.capability is not capability
                    or grant.scope is not scope
                    or grant.expires_at_ms is not expiry
                    for grant, capability, scope, expiry in grant_epoch
                    for carrier in (grant,)
                )
                or not _denials_still_false(receipt)
                or any(value is not first for value, first in zip(
                    (
                        receipt.topology_digest, receipt.registry_revision,
                        receipt.wave_bound_step_hashes, receipt.final_status_digest,
                        receipt.fingerprint,
                    ), original, strict=True,
                ))
                or plan.topology_digest() != topology
                or plan.status_digest() != status
                or registry.revision != revision
            ):
                raise DisconnectedReadCycleReceiptRejected("READ receipt or inputs changed")
        except DisconnectedReadCycleReceiptRejected:
            raise
        except (AttributeError, KeyError, TypeError, ValueError, PlanConflictError) as exc:
            raise DisconnectedReadCycleReceiptRejected("READ receipt epoch invalid") from exc

    stable()
    try:
        fresh = simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=observed_at_ms,
        )
    except (DisconnectedReadCycleRejected, TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedReadCycleReceiptRejected("fresh mock READ simulation denied") from exc

    stable()
    if type(fresh) is not _RECEIPT:
        raise DisconnectedReadCycleReceiptRejected("fresh mock receipt type changed")
    fresh_epoch = (
        fresh.topology_digest, fresh.registry_revision,
        fresh.wave_bound_step_hashes, fresh.final_status_digest, fresh.fingerprint,
    )

    def fresh_stable() -> None:
        _require_original_denials(fresh)
        if (
            type(fresh) is not _RECEIPT
            or fresh_epoch != original
            or any(value is not first for value, first in zip(
                (
                    fresh.topology_digest, fresh.registry_revision,
                    fresh.wave_bound_step_hashes, fresh.final_status_digest,
                    fresh.fingerprint,
                ), fresh_epoch, strict=True,
            ))
            or not _denials_still_false(fresh)
            or any(value is not first for value, first in zip(
                (
                    fresh.topology_digest, fresh.registry_revision,
                    fresh.wave_bound_step_hashes, fresh.final_status_digest,
                    fresh.fingerprint,
                ), fresh_epoch, strict=True,
            ))
        ):
            raise DisconnectedReadCycleReceiptRejected("mock READ receipt differs")

    fresh_stable()
    stable()
    fresh_stable()
    stable()
    return None
