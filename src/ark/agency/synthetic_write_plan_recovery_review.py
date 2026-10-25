"""Bounded disconnected plan-wide WRITE recovery diagnosis.

This aggregates every WRITE step in a synthetic journal. It never dispatches
tools, issues permissions, authorizes replay, or attests an external outcome.
Each SQLite store remains independently committed, NOT an atomic snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .audit import SQLiteActionAudit
from .audit_continuity_review import AuditContinuityWitness
from .contracts import Effect, ToolCall
from .planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail
from .registry import ToolRegistry
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
)
from .synthetic_occurrence_continuity_review import SyntheticLedgerWitness
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
    # Diagnoses only: descendants are held, never authorized or replayed.
    downstream_write_hold_step_ids: tuple[str, ...] = ()
    terminally_blocked_write_step_ids: tuple[str, ...] = ()

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
    retained_plan: SyntheticPlanTail | None = None,
    retained_ledger: SyntheticLedgerWitness | None = None,
    retained_audit: AuditContinuityWitness | None = None,
    retained_link: SyntheticAuditLinkWitness | None = None,
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
        or retained_plan is not None and type(retained_plan) is not SyntheticPlanTail
        or retained_ledger is not None
        and type(retained_ledger) is not SyntheticLedgerWitness
        or retained_audit is not None
        and type(retained_audit) is not AuditContinuityWitness
        or retained_link is not None
        and type(retained_link) is not SyntheticAuditLinkWitness
        or retained_link is not None and link_store is None
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
        # Retained evidence must remain the same caller-held epoch throughout
        # every independent per-step replay, including its original carriers.
        retained_epoch = tuple(
            (
                witness,
                tuple((field.name, getattr(witness, field.name))
                      for field in fields(witness)),
            )
            for witness in (
                retained_plan, retained_ledger, retained_audit, retained_link,
            )
            if witness is not None
        )
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
                and all(
                    getattr(witness, field_name) is original
                    for witness, originals in retained_epoch
                    for field_name, original in originals
                )
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
        baseline = journal.recover(retained=retained_plan)
        assert_epoch()
        reviews = []
        witness_epoch = None
        # Returned recovery witnesses are frozen dataclasses, not immutable
        # under reflective object.__setattr__. A later per-step callback can
        # retarget an earlier review without touching the input PlanGraph.
        # Pin each returned nested carrier immediately and recheck all prior
        # reviews at every independent SQLite read boundary.
        review_epochs = []

        def assert_review_epochs() -> None:
            try:
                if any(
                    getattr(entity, field_name) is not original
                    for carriers in review_epochs
                    for entity, pinned_fields in carriers
                    for field_name, original in pinned_fields
                ):
                    raise SyntheticWritePlanReviewRejected(
                        "synthetic plan returned review changed during diagnosis"
                    )
            except (TypeError, AttributeError) as exc:
                raise SyntheticWritePlanReviewRejected(
                    "synthetic plan returned review malformed during diagnosis"
                ) from exc

        for name, call in sorted(write_steps):
            assert_epoch()
            assert_review_epochs()
            reviewed = review_synthetic_write_recovery(
                journal, ledger_path, audit, registry, call,
                step_id=name, link_store=link_store,
                retained_plan=retained_plan,
                retained_ledger=retained_ledger,
                retained_audit=retained_audit,
                retained_link=retained_link,
            )
            assert_epoch()
            assert_review_epochs()
            if type(reviewed) is not SyntheticRecoveryReview:
                raise SyntheticWritePlanReviewRejected(
                    "exact synthetic per-step recovery review required"
                )
            carriers = tuple(
                (
                    entity,
                    tuple((field.name, getattr(entity, field.name))
                          for field in fields(entity)),
                )
                for entity in (
                    reviewed, reviewed.plan_tail, reviewed.ledger_witness,
                    reviewed.audit_witness, reviewed.link_witness,
                )
                if entity is not None
            )
            review_epochs.append(carriers)
            assert_review_epochs()
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
        assert_review_epochs()
        repeated = review_synthetic_write_recovery(
            journal, ledger_path, audit, registry, first_call,
            step_id=first_name, link_store=link_store,
            retained_plan=retained_plan,
            retained_ledger=retained_ledger,
            retained_audit=retained_audit,
            retained_link=retained_link,
        )
        assert_epoch()
        assert_review_epochs()
        if repeated != reviews[0] or journal.recover(retained=retained_plan) != baseline:
            raise SyntheticWritePlanReviewRejected(
                "synthetic plan evidence changed during final recheck"
            )
        uncertain = tuple(sorted(
            item.step_id for item in reviews
            if item.ambiguous_write
            or item.matching_occurrences
            or item.matching_audit_links
        ))
        # A locally PENDING successor is not independently safe when its
        # prerequisite WRITE is uncertain. Propagate through READ bridges too.
        # Keep this distinct from a direct UNKNOWN outcome: descendants need
        # a hold, not a fabricated external result or a retry instruction.
        dependencies = {
            name: original_dependencies
            for (_step, name, _call, original_dependencies, *_rest) in snapshots
        }
        write_names = {name for name, _call in write_steps}

        def downstream(
            roots: set[str], *, exclude_direct_roots: bool,
        ) -> tuple[str, ...]:
            reached = set(roots)
            descendants: set[str] = set()
            while True:
                additions = {
                    name for name, upstream in dependencies.items()
                    if name not in descendants and any(
                        dependency in reached for dependency in upstream
                    )
                }
                if not additions:
                    break
                descendants.update(additions)
                reached.update(additions)
            # PlanGraph may mark downstream nodes BLOCKED automatically.
            # Those nodes are still descendants of a terminal prerequisite,
            # even when they themselves appear in the terminal root set.
            if exclude_direct_roots:
                descendants.difference_update(roots)
            return tuple(sorted(descendants & write_names))

        terminal = {
            name for name, state, _revision in baseline.step_statuses
            if state in {"failed", "blocked", "cancelled"}
        }
        downstream_hold = downstream(set(uncertain), exclude_direct_roots=True)
        terminal_hold = downstream(terminal, exclude_direct_roots=False)
        assert_epoch()
        assert_review_epochs()
        return SyntheticWritePlanReview(
            tuple(reviews), uncertain, baseline.tail.topology_digest,
            downstream_hold, terminal_hold,
        )
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise SyntheticWritePlanReviewRejected(
            "synthetic plan registry or evidence malformed"
        ) from exc
