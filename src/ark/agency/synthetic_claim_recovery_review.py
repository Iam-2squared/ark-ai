"""Deny-only synthetic approval and four-store WRITE recovery correlation.

This module checks two local cancellation fences around a cross-store recovery
review. Neither those reads nor matching hashes provide authenticated consent,
a global transaction, backend effect proof, or permission to retry a WRITE.
An append after the final check can still occur; live dispatch is impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .audit import SQLiteActionAudit
from .audit_continuity_review import AuditContinuityWitness
from .contracts import ToolCall
from .planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail
from .registry import ToolRegistry
from .synthetic_approval_cancellation_fence_review import (
    review_synthetic_approval_cancellation_fence,
)
from .synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationWitness,
)
from .synthetic_approval_claim_review import SyntheticApprovalEnvelope
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
)
from .synthetic_occurrence_continuity_review import SyntheticLedgerWitness
from .synthetic_recovery_triage import review_synthetic_write_recovery


class SyntheticClaimRecoveryRejected(RuntimeError):
    """The disconnected approval/recovery identities or epochs do not agree."""


@dataclass(frozen=True, slots=True)
class SyntheticClaimRecoveryReview:
    """Identity-only local diagnosis, with every execution authority denied."""

    approval_id: str
    registry_revision: str
    bound_action_id: str
    request_id: str
    step_id: str
    step_state: str
    ambiguous_write: bool
    matching_occurrences: tuple[str, ...]
    cancellation_event_count: int
    cancellation_tail_hash: str
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

    @property
    def external_outcome_known(self) -> bool:
        return False


def _claim_epoch(value: SyntheticApprovalEnvelope) -> tuple[object, ...]:
    return tuple(getattr(value, field.name) for field in fields(SyntheticApprovalEnvelope))


def review_synthetic_claim_write_recovery(
    envelope: SyntheticApprovalEnvelope,
    cancellation: SyntheticCancellationLedger,
    journal: SyntheticPlanJournal,
    ledger_path: Path,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    step_id: str,
    issuer_digest: str,
    subject_digest: str,
    purpose_digest: str,
    recipient_digest: str,
    now_ms: int,
    retained_cancellation: SyntheticCancellationWitness | None = None,
    retained_plan: SyntheticPlanTail | None = None,
    retained_ledger: SyntheticLedgerWitness | None = None,
    retained_audit: AuditContinuityWitness | None = None,
    link_store: SyntheticOccurrenceAuditLinkStore | None = None,
    retained_link: SyntheticAuditLinkWitness | None = None,
) -> SyntheticClaimRecoveryReview:
    """Reconcile local evidence with two veto checks; never grant execution.

    Two cancellation reads flank the independent plan/reservation/audit/link
    reads. All local epochs are checked again before returning. This cannot
    close a post-review cancellation race or attest a real-world WRITE.
    """
    if type(envelope) is not SyntheticApprovalEnvelope:
        raise SyntheticClaimRecoveryRejected("exact synthetic approval envelope required")
    initial = _claim_epoch(envelope)
    claim_args = {
        "issuer_digest": issuer_digest,
        "subject_digest": subject_digest,
        "purpose_digest": purpose_digest,
        "recipient_digest": recipient_digest,
        "now_ms": now_ms,
    }
    first = review_synthetic_approval_cancellation_fence(
        envelope, registry, call, cancellation,
        retained=retained_cancellation, **claim_args,
    )
    recovery = review_synthetic_write_recovery(
        journal, ledger_path, audit, registry, call,
        step_id=step_id, retained_plan=retained_plan,
        retained_ledger=retained_ledger, retained_audit=retained_audit,
        link_store=link_store, retained_link=retained_link,
    )
    second = review_synthetic_approval_cancellation_fence(
        envelope, registry, call, cancellation,
        retained=retained_cancellation, **claim_args,
    )
    if (
        first != second
        or _claim_epoch(envelope) != initial
        or recovery.bound_action_id != envelope.bound_action_id
        or recovery.registry_revision != envelope.registry_revision
        or recovery.request_id != envelope.request_id
        or recovery.step_id != step_id
        or first.approval_id != envelope.approval_id
    ):
        raise SyntheticClaimRecoveryRejected(
            "approval, recovery or cancellation state changed during review"
        )
    return SyntheticClaimRecoveryReview(
        first.approval_id, recovery.registry_revision,
        recovery.bound_action_id, recovery.request_id,
        recovery.step_id, recovery.step_state, recovery.ambiguous_write,
        recovery.matching_occurrences, first.cancellation_event_count,
        first.cancellation_tail_hash, now_ms,
    )
