"""Deny-only correlation of a claimed approval pair with Planner recovery.

An association is locally reproducible, NOT authenticated human consent or
proof that a WRITE happened. No action, replay, or notification is issued.
The independent SQLite reads cannot form an atomic global snapshot and
a post-review write or cancellation can still race with consumption.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from pathlib import Path

from .audit import SQLiteActionAudit
from .audit_continuity_review import AuditContinuityWitness
from .contracts import ToolCall
from .planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail
from .registry import ToolRegistry
from .synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationWitness,
)
from .synthetic_approval_claim_review import SyntheticApprovalEnvelope
from .synthetic_claim_occurrence_link_review import (
    SyntheticClaimLinkWitness,
    SyntheticClaimOccurrenceLinkStore,
)
from .synthetic_claim_occurrence_recheck_review import (
    review_synthetic_claim_occurrence_sources,
)
from .synthetic_claim_recovery_review import review_synthetic_claim_write_recovery
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
)
from .synthetic_occurrence_continuity_review import SyntheticLedgerWitness

_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")


class SyntheticClaimProvenanceRejected(RuntimeError):
    """The disconnected claim, source and recovery epochs cannot agree."""


@dataclass(frozen=True, slots=True)
class SyntheticClaimProvenanceReview:
    approval_id: str
    occurrence_id: str
    request_id: str
    registry_revision: str
    bound_action_id: str
    step_id: str
    step_state: str
    ambiguous_write: bool
    claim_link_count: int
    claim_link_tail_hash: str
    reservation_digest: str
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


def _epoch(value: SyntheticApprovalEnvelope) -> tuple[object, ...]:
    return tuple(getattr(value, field.name) for field in fields(SyntheticApprovalEnvelope))


def review_synthetic_claim_write_provenance(
    envelope: SyntheticApprovalEnvelope,
    cancellation: SyntheticCancellationLedger,
    journal: SyntheticPlanJournal,
    ledger_path: Path,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    call: ToolCall,
    claim_links: SyntheticClaimOccurrenceLinkStore,
    *,
    step_id: str,
    occurrence_id: str,
    issuer_digest: str,
    subject_digest: str,
    purpose_digest: str,
    recipient_digest: str,
    now_ms: int,
    retained_cancellation: SyntheticCancellationWitness | None = None,
    retained_plan: SyntheticPlanTail | None = None,
    retained_ledger: SyntheticLedgerWitness | None = None,
    retained_audit: AuditContinuityWitness | None = None,
    audit_links: SyntheticOccurrenceAuditLinkStore | None = None,
    retained_audit_links: SyntheticAuditLinkWitness | None = None,
    retained_claim_links: SyntheticClaimLinkWitness | None = None,
) -> SyntheticClaimProvenanceReview:
    """Require an exact saved pair and a single matching recovery occurrence.

    A/B/A/B observations detect visible intervening drift in either path.
    They cannot certify the issuer, recipient, clock, historical consent, an
    atomic multi-store snapshot or a real backend effect. UNKNOWN stays UNKNOWN.
    """
    if (
        type(envelope) is not SyntheticApprovalEnvelope
        or type(claim_links) is not SyntheticClaimOccurrenceLinkStore
        or not isinstance(ledger_path, Path)
        or type(occurrence_id) is not str
        or not _OCCURRENCE.fullmatch(occurrence_id)
    ):
        raise SyntheticClaimProvenanceRejected("exact claim provenance inputs required")
    claim_epoch = _epoch(envelope)
    # Pin identities of *all* disconnected stores, not only the association
    # sidecar. A final source callback can retarget another store after its
    # own last review; value-equal Path replacements must also be rejected.
    source_epoch = (
        cancellation.path, journal._path, audit.path, claim_links.path,
        None if audit_links is None else audit_links.path,
    )
    if any(path is not None and not isinstance(path, Path) for path in source_epoch):
        raise SyntheticClaimProvenanceRejected("exact provenance sources required")
    if type(call) is not ToolCall:
        raise SyntheticClaimProvenanceRejected("exact provenance ToolCall required")
    call_arguments = call.arguments
    call_epoch = (
        call.tool, call.capability, call.scope,
        call.request_id, call.arguments_sha256,
    )
    registry_epoch = registry.revision
    arguments = dict(
        step_id=step_id,
        issuer_digest=issuer_digest,
        subject_digest=subject_digest,
        purpose_digest=purpose_digest,
        recipient_digest=recipient_digest,
        now_ms=now_ms,
        retained_cancellation=retained_cancellation,
        retained_plan=retained_plan,
        retained_ledger=retained_ledger,
        retained_audit=retained_audit,
        link_store=audit_links,
        retained_link=retained_audit_links,
    )
    source_arguments = dict(
        expected_pair=(envelope.approval_id, occurrence_id),
        retained_links=retained_claim_links,
        retained_reservations=retained_ledger,
    )
    first = review_synthetic_claim_write_recovery(
        envelope, cancellation, journal, ledger_path, audit, registry, call,
        **arguments,
    )
    if first.matching_occurrences != (occurrence_id,):
        raise SyntheticClaimProvenanceRejected(
            "recovery requires exactly one matching claimed occurrence"
        )
    source_first = review_synthetic_claim_occurrence_sources(
        claim_links, ledger_path, **source_arguments,
    )
    second = review_synthetic_claim_write_recovery(
        envelope, cancellation, journal, ledger_path, audit, registry, call,
        **arguments,
    )
    source_second = review_synthetic_claim_occurrence_sources(
        claim_links, ledger_path, **source_arguments,
    )
    current_sources = (
        cancellation.path, journal._path, audit.path, claim_links.path,
        None if audit_links is None else audit_links.path,
    )
    if (
        first != second
        or source_first != source_second
        or not source_first.expected_pair_found
        or _epoch(envelope) != claim_epoch
        or any(
            current is not original
            for current, original in zip(current_sources, source_epoch, strict=True)
        )
        or call.arguments is not call_arguments
        or (
            call.tool, call.capability, call.scope,
            call.request_id, call.arguments_sha256,
        ) != call_epoch
        or registry.revision != registry_epoch
        or first.approval_id != envelope.approval_id
        or first.request_id != envelope.request_id
        or first.registry_revision != envelope.registry_revision
        or first.bound_action_id != envelope.bound_action_id
    ):
        raise SyntheticClaimProvenanceRejected(
            "claim, source, cancellation or recovery changed during review"
        )
    return SyntheticClaimProvenanceReview(
        first.approval_id, occurrence_id, first.request_id,
        first.registry_revision, first.bound_action_id, first.step_id,
        first.step_state, first.ambiguous_write,
        source_first.link_event_count, source_first.link_tail_hash,
        source_first.reservation_digest, first.cancellation_tail_hash, now_ms,
    )
