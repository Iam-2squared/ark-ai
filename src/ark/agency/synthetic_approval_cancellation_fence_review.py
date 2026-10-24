"""Read-only synthetic approval + persisted cancellation pre/post fence.

No authentic consent, trusted clock, real ToolBackend, or dispatch occurs.
Two local SQLite reads do not form an atomic grant or remove the post-check
revocation race. Any change to the veto log during review is denied, even
when it belongs to an unrelated claim. The retained witness must be stored
separately to detect a coherently rewritten historical cancellation journal.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .contracts import ToolCall
from .registry import ToolRegistry
from .synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationWitness,
)
from .synthetic_approval_claim_review import (
    SyntheticApprovalEnvelope,
    review_synthetic_approval_claim,
)

_MAX = 2**63 - 1


class SyntheticApprovalFenceRejected(RuntimeError):
    """The local claim/cancellation diagnostic failed closed."""


@dataclass(frozen=True, slots=True)
class SyntheticApprovalFenceReview:
    approval_id: str
    bound_action_id: str
    cancellation_tail_hash: str
    cancellation_event_count: int
    observed_at_ms: int

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _epoch(envelope: SyntheticApprovalEnvelope) -> tuple[object, ...]:
    return tuple(getattr(envelope, field.name) for field in fields(SyntheticApprovalEnvelope))


def review_synthetic_approval_cancellation_fence(
    envelope: SyntheticApprovalEnvelope,
    registry: ToolRegistry,
    call: ToolCall,
    ledger: SyntheticCancellationLedger,
    *,
    issuer_digest: str,
    subject_digest: str,
    purpose_digest: str,
    recipient_digest: str,
    now_ms: int,
    retained: SyntheticCancellationWitness | None = None,
) -> SyntheticApprovalFenceReview:
    """Diagnostic only: bracket a registry-bound claim by durable veto reads.

    A successful local match reports *no* authorization: neither missing
    cancellation nor hash-linked history proves authenticated user consent.
    """
    if (
        type(envelope) is not SyntheticApprovalEnvelope
        or type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(ledger) is not SyntheticCancellationLedger
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or retained is not None and type(retained) is not SyntheticCancellationWitness
    ):
        raise SyntheticApprovalFenceRejected("exact disconnected approval fence inputs required")
    original = _epoch(envelope)
    source_epoch = ledger.path
    if not isinstance(source_epoch, Path):
        raise SyntheticApprovalFenceRejected("exact claim cancellation source required")
    arguments_epoch = call.arguments
    call_epoch = (
        call.tool, call.capability, call.scope,
        call.request_id, call.arguments_sha256,
    )
    registry_epoch = registry.revision
    retained_epoch = (
        None if retained is None
        else tuple(getattr(retained, field.name) for field in fields(retained))
    )

    def assert_epoch() -> None:
        if (
            ledger.path is not source_epoch
            or _epoch(envelope) != original
            or call.arguments is not arguments_epoch
            or (
                call.tool, call.capability, call.scope,
                call.request_id, call.arguments_sha256,
            ) != call_epoch
            or registry.revision != registry_epoch
            or retained is not None
            and tuple(getattr(retained, field.name) for field in fields(retained))
            != retained_epoch
        ):
            raise SyntheticApprovalFenceRejected(
                "claim fence input, source or retained history changed during review"
            )

    first = ledger.review_state(envelope.approval_id, retained=retained)
    assert_epoch()
    if (
        first.approval_id != original[0]
        or first.cancelled
        or first.witness.last_cancelled_at_ms > now_ms
    ):
        raise SyntheticApprovalFenceRejected("claim cancelled or synthetic clock regressed")
    result = review_synthetic_approval_claim(
        envelope, registry, call,
        issuer_digest=issuer_digest,
        subject_digest=subject_digest,
        purpose_digest=purpose_digest,
        recipient_digest=recipient_digest,
        now_ms=now_ms,
        cancelled_ids=frozenset(),
    )
    assert_epoch()
    second = ledger.review_state(original[0], retained=first.witness)
    assert_epoch()
    if (
        second.approval_id != original[0]
        or second.cancelled
        or second.witness != first.witness
        or second.witness.last_cancelled_at_ms > now_ms
        or _epoch(envelope) != original
        or result.approval_id != original[0]
        or result.bound_action_id != envelope.bound_action_id
    ):
        raise SyntheticApprovalFenceRejected(
            "cancellation/claim state changed during disconnected review"
        )
    assert_epoch()
    return SyntheticApprovalFenceReview(
        result.approval_id, result.bound_action_id,
        second.witness.tail_hash, second.witness.event_count, now_ms,
    )
