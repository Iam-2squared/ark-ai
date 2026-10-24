"""Bounded disconnected plan-wide WRITE recovery diagnosis.

This aggregates every WRITE step in a synthetic journal. It never dispatches
tools, issues permissions, authorizes replay, or attests an external outcome.
Each SQLite store remains independently committed, NOT an atomic snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .audit import SQLiteActionAudit
from .contracts import Effect, ToolCall
from .planner_journal_review import SyntheticPlanJournal
from .registry import ToolRegistry
from .synthetic_occurrence_audit_link_review import SyntheticOccurrenceAuditLinkStore
from .synthetic_recovery_triage import (
    SyntheticRecoveryReview,
    review_synthetic_write_recovery,
)

_MAX_PLAN_STEPS = 128


class SyntheticWritePlanReviewRejected(RuntimeError):
    """Plan-wide synthetic recovery could not establish stable evidence."""


@dataclass(frozen=True, slots=True)
class SyntheticWritePlanReview:
    """Diagnostic only; no recovered object carries execution authority."""

    steps: tuple[SyntheticRecoveryReview, ...]
    uncertain_step_ids: tuple[str, ...]
    plan_topology_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def review_synthetic_write_plan(
    journal: SyntheticPlanJournal,
    ledger_path: Path,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    *,
    link_store: SyntheticOccurrenceAuditLinkStore | None = None,
) -> SyntheticWritePlanReview:
    """Check all WRITE step identities without calling any ToolBackend.

    A PENDING step with a separately persisted reservation remains *uncertain*
    rather than safe to start: journal-only state never overrides occurrence
    evidence. The original per-step journal states are not reclassified.
    """
    if (
        type(journal) is not SyntheticPlanJournal
        or not isinstance(ledger_path, Path)
        or type(audit) is not SQLiteActionAudit
        or type(registry) is not ToolRegistry
        or link_store is not None
        and type(link_store) is not SyntheticOccurrenceAuditLinkStore
    ):
        raise SyntheticWritePlanReviewRejected("exact synthetic plan stores required")
    topology = journal._steps
    if type(topology) is not tuple or not 1 <= len(topology) <= _MAX_PLAN_STEPS:
        raise SyntheticWritePlanReviewRejected("synthetic plan review budget exceeded")
    try:
        snapshots = tuple(
            (
                step, step.step_id, step.call, step.depends_on,
                step.call.arguments, step.call.request_id,
                (
                    step.call.tool, step.call.capability, step.call.scope,
                    step.call.arguments_sha256,
                ),
            )
            for step in topology
        )
        sources = (
            journal._path, audit.path,
            None if link_store is None else link_store._path,
        )
        registry_revision = registry.revision
    except (AttributeError, TypeError, ValueError) as exc:
        raise SyntheticWritePlanReviewRejected("synthetic plan identity invalid") from exc

    def assert_epoch() -> None:
        try:
            current_sources = (
                journal._path, audit.path,
                None if link_store is None else link_store._path,
            )
            stable = (
                journal._steps is topology
                and all(
                    current is initial
                    for current, initial in zip(
                        current_sources, sources, strict=True,
                    )
                )
                and registry.revision == registry_revision
                and len(journal._steps) == len(snapshots)
                and all(
                    step.step_id == name
                    and step.call is call
                    and step.depends_on is dependencies
                    and step.call.arguments is arguments
                    and step.call.request_id == request
                    and type(call) is ToolCall
                    and (
                        call.tool, call.capability, call.scope,
                        call.arguments_sha256,
                    ) == call_identity
                    for (
                        step, name, call, dependencies, arguments, request,
                        call_identity,
                    ) in snapshots
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise SyntheticWritePlanReviewRejected(
                "synthetic plan input epoch changed"
            ) from exc
        if not stable:
            raise SyntheticWritePlanReviewRejected("synthetic plan input epoch changed")

    try:
        write_steps = []
        seen_requests = set()
        for (
            _step, name, call, _dependencies, _arguments, request, _call_identity,
        ) in snapshots:
            assert_epoch()
            bound = registry.bind(call)
            assert_epoch()
            # Reentrant binding can resolve another ToolCall then restore
            # the caller's fields before returning. Verify its exact subject.
            if (
                bound.call is not call
                or bound.call.request_id != request
                or bound.registry_revision != registry_revision
                or bound.registration is not registry.get(call.tool)
            ):
                raise SyntheticWritePlanReviewRejected(
                    "synthetic plan registry binding changed during review"
                )
            assert_epoch()
            if bound.registration.effect is Effect.WRITE:
                if request in seen_requests:
                    raise SyntheticWritePlanReviewRejected(
                        "multiple WRITE steps share a request identity"
                    )
                seen_requests.add(request)
                write_steps.append((name, call))
        if not write_steps:
            raise SyntheticWritePlanReviewRejected("no synthetic WRITE steps to review")
        baseline = journal.recover()
        assert_epoch()
        reviews = []
        witness_epoch = None
        for name, call in sorted(write_steps):
            assert_epoch()
            reviewed = review_synthetic_write_recovery(
                journal, ledger_path, audit, registry, call,
                step_id=name, link_store=link_store,
            )
            assert_epoch()
            witnesses = (
                reviewed.plan_tail, reviewed.ledger_witness,
                reviewed.audit_witness, reviewed.link_witness,
            )
            if reviewed.plan_tail != baseline.tail or (
                witness_epoch is not None and witnesses != witness_epoch
            ):
                raise SyntheticWritePlanReviewRejected(
                    "synthetic WRITE stores changed across plan reviews"
                )
            if witness_epoch is None:
                witness_epoch = witnesses
            reviews.append(reviewed)
        first_name, first_call = min(write_steps)
        repeated = review_synthetic_write_recovery(
            journal, ledger_path, audit, registry, first_call,
            step_id=first_name, link_store=link_store,
        )
        assert_epoch()
        if repeated != reviews[0] or journal.recover() != baseline:
            raise SyntheticWritePlanReviewRejected(
                "synthetic plan evidence changed during final recheck"
            )
        uncertain = tuple(sorted(
            item.step_id for item in reviews
            if item.ambiguous_write
            or item.matching_occurrences
            or item.matching_audit_links
        ))
        return SyntheticWritePlanReview(
            tuple(reviews), uncertain, baseline.tail.topology_digest,
        )
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise SyntheticWritePlanReviewRejected(
            "synthetic plan registry or evidence malformed"
        ) from exc
