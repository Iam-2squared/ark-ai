"""Read-only, disconnected cross-store recovery diagnosis for synthetic WRITE.

This review observes three independently committed SQLite stores. It is NOT
a cross-store transaction, external action receipt, authorization, or replay
instruction. A reservation and an audit event can never prove side effects.
All clocks, registrations, and retained witnesses are caller supplied.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass, fields
from pathlib import Path

from .audit import SQLiteActionAudit
from .audit_continuity_review import (
    AuditContinuityWitness,
    review_audit_continuity,
)
from .contracts import Effect, ToolCall
from .durable_occurrence_review import _validate
from .planner import PlanGraph
from .planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanTail,
)
from .registry import ToolRegistry
from .synthetic_occurrence_audit_link_review import (
    _SELECT as _LINK_ROWS,
)
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
    _audit_identity,
)
from .synthetic_occurrence_audit_link_review import (
    _hash as _link_hash,
)
from .synthetic_occurrence_audit_link_review import (
    _replay as _replay_links,
)
from .synthetic_occurrence_continuity_review import (
    _COLUMNS,
    SyntheticLedgerWitness,
    _digest,
    assert_synthetic_history_continues,
    read_synthetic_ledger_witness,
)


class SyntheticRecoveryRejected(RuntimeError):
    """Cannot give even a coherent disconnected recovery diagnosis."""


@dataclass(frozen=True, slots=True)
class SyntheticRecoveryReview:
    """Diagnostic evidence from independent snapshots, never authority."""

    step_id: str
    request_id: str
    registry_revision: str
    bound_action_id: str
    step_state: str
    ambiguous_write: bool
    plan_tail: SyntheticPlanTail
    ledger_witness: SyntheticLedgerWitness
    audit_witness: AuditContinuityWitness
    matching_occurrences: tuple[str, ...]
    link_witness: SyntheticAuditLinkWitness | None = None
    matching_audit_links: tuple[tuple[str, int], ...] = ()

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def review_synthetic_write_recovery(
    journal: SyntheticPlanJournal,
    ledger_path: Path,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    step_id: str,
    retained_plan: SyntheticPlanTail | None = None,
    retained_ledger: SyntheticLedgerWitness | None = None,
    retained_audit: AuditContinuityWitness | None = None,
    link_store: SyntheticOccurrenceAuditLinkStore | None = None,
    retained_link: SyntheticAuditLinkWitness | None = None,
) -> SyntheticRecoveryReview:
    """Compare synthetic identities without side effects or retry authority.

    Each of the plan, ledger and audit reviews holds its own coherent SQLite
    read transaction; there is deliberately NO global cross-store snapshot.
    Even all-matching receipts cannot resolve an external WRITE outcome.
    """
    if (
        type(journal) is not SyntheticPlanJournal
        or not isinstance(ledger_path, Path)
        or type(audit) is not SQLiteActionAudit
        or type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(step_id) is not str
        or not step_id
    ):
        raise SyntheticRecoveryRejected("recovery requires exact fixture inputs")
    if (
        retained_plan is not None and type(retained_plan) is not SyntheticPlanTail
        or retained_ledger is not None
        and type(retained_ledger) is not SyntheticLedgerWitness
        or retained_audit is not None
        and type(retained_audit) is not AuditContinuityWitness
        or link_store is not None
        and type(link_store) is not SyntheticOccurrenceAuditLinkStore
        or retained_link is not None
        and type(retained_link) is not SyntheticAuditLinkWitness
        or retained_link is not None and link_store is None
    ):
        raise SyntheticRecoveryRejected("retained witnesses must use exact types")

    if retained_link is not None:
        retained_link.assert_shape()

    # Direct callers must pin the complete input epoch themselves. Higher-level
    # claim wrappers cannot be relied on when this diagnostic is used alone.
    source_epoch = (
        journal._path, audit.path,
        None if link_store is None else link_store._path,
    )
    if any(path is not None and not isinstance(path, Path) for path in source_epoch):
        raise SyntheticRecoveryRejected("recovery requires stable Path sources")
    topology_epoch = journal._steps
    # The outer tuple alone does not freeze its reflected-mutable PlanSteps.
    # Pin each step's original action and dependency carriers before bind().
    topology_items = tuple(
        (
            step, step.step_id, step.call, step.depends_on,
            step.call.arguments, step.call.request_id,
        )
        for step in topology_epoch
    )
    arguments_epoch = call.arguments
    call_epoch = (
        call.tool, call.capability, call.scope,
        call.request_id, call.arguments_sha256,
    )
    registry_epoch = registry.revision
    retained_epochs = tuple(
        (witness, tuple(getattr(witness, field.name) for field in fields(witness)))
        for witness in (retained_plan, retained_ledger, retained_audit, retained_link)
        if witness is not None
    )

    def assert_epoch() -> None:
        current_sources = (
            journal._path, audit.path,
            None if link_store is None else link_store._path,
        )
        if (
            any(now is not before for now, before in zip(
                current_sources, source_epoch, strict=True,
            ))
            or journal._steps is not topology_epoch
            or any(
                step.step_id != step_id_before
                or step.call is not original_call
                or step.depends_on is not original_dependencies
                or step.call.arguments is not original_arguments
                or step.call.request_id != original_request
                for (
                    step, step_id_before, original_call,
                    original_dependencies, original_arguments, original_request,
                ) in topology_items
            )
            or call.arguments is not arguments_epoch
            or (
                call.tool, call.capability, call.scope,
                call.request_id, call.arguments_sha256,
            ) != call_epoch
            or registry.revision != registry_epoch
            or any(
                tuple(getattr(witness, field.name) for field in fields(witness)) != original
                for witness, original in retained_epochs
            )
        ):
            raise SyntheticRecoveryRejected(
                "recovery input, retained witness or source changed during review"
            )

    try:
        first = registry.bind(call)
        assert_epoch()
        if first.registration.effect is not Effect.WRITE:
            raise SyntheticRecoveryRejected("only WRITE fixtures may be reviewed")
        # The journal's persisted topology is checked by recover(). Do not
        # infer an identity match from a step name alone.
        topology = PlanGraph(journal._steps)
        assert_epoch()
        if step_id not in topology.steps:
            raise SyntheticRecoveryRejected("step is not in the plan topology")
        if topology.steps[step_id].call.request_id != first.call.request_id:
            raise SyntheticRecoveryRejected("plan step action identity differs")
        plan = journal.recover(retained=retained_plan)
        assert_epoch()
        state = dict((name, value) for name, value, _ in plan.step_statuses)
        if step_id not in state:
            raise SyntheticRecoveryRejected("step is missing from recovery")
        # Ledger identities and their witness MUST be collected from the SAME
        # read transaction. A separate earlier/later witness would be racy.
        # An overridable Path resolver, URI builder or connection opener
        # may change an earlier input before the first ledger SELECT. Check
        # every boundary here, not only after a complete ledger review:
        # a later audit callback could otherwise restore temporary drift.
        resolved_ledger = ledger_path.resolve()
        assert_epoch()
        uri = resolved_ledger.as_uri() + "?mode=ro"
        assert_epoch()
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            assert_epoch()
            conn.execute("BEGIN")
            try:
                _validate(conn)
                rows = tuple(conn.execute(_COLUMNS))
                hashes = tuple(sorted(
                    _digest("ARK-reservation-row-v1", row) for row in rows
                ))
                ledger = SyntheticLedgerWitness(
                    hashes,
                    "synthetic_ledger_" + _digest("ARK-ledger-v1", hashes),
                )
                ledger.assert_integrity()
                if retained_ledger is not None:
                    assert_synthetic_history_continues(retained_ledger, ledger)
                relevant = tuple(row for row in rows if row[4] == first.call.request_id)
                if any(
                    row[2] != first.registry_revision
                    or row[3] != first.bound_action_id
                    for row in relevant
                ):
                    raise SyntheticRecoveryRejected(
                        "stored request has a conflicting registry binding"
                    )
                occurrences = tuple(sorted(row[1] for row in relevant))
                stored_reservations = {row[1]: row for row in rows}
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        # A later audit callback could restore inputs mutated during the
        # ledger replay. Do not defer the input check until that callback.
        assert_epoch()
        audit_witness = review_audit_continuity(
            audit, retained=retained_audit, require_monotonic_time=True,
        )
        assert_epoch()
        link_witness = None
        matching_links: tuple[tuple[str, int], ...] = ()
        if link_store is not None:
            # A sidecar witness and its rows MUST share one sidecar snapshot.
            # Reservation and audit snapshots remain separately committed.
            with closing(link_store._connect(readonly=True)) as link_conn:
                link_conn.execute("BEGIN")
                try:
                    prefixes = _replay_links(link_conn)
                    assert_epoch()
                    if retained_link is not None and (
                        retained_link.event_count >= len(prefixes)
                        or prefixes[retained_link.event_count] != retained_link
                    ):
                        raise SyntheticRecoveryRejected(
                            "retained occurrence-audit link history changed"
                        )
                    link_rows = tuple(link_conn.execute(_LINK_ROWS))
                    assert_epoch()
                    pairs: list[tuple[str, int]] = []
                    for row in link_rows:
                        (_seq, occurrence, revision, bound, request,
                         event_id, event_digest, linked_at, _previous, _hash) = row
                        reservation = stored_reservations.get(occurrence)
                        if (
                            reservation is None
                            or (revision, bound, request) != reservation[2:5]
                            or reservation[5] > linked_at
                        ):
                            raise SyntheticRecoveryRejected(
                                "sidecar link has no matching stored reservation"
                            )
                        events = audit.events(after_event_id=event_id - 1, limit=1)
                        assert_epoch()
                        if len(events) != 1 or events[0].event_id != event_id:
                            raise SyntheticRecoveryRejected(
                                "sidecar link has no matching audit event"
                            )
                        event = events[0]
                        if (
                            event.request_id != request
                            or event.outcome != "synthetic_audit_before_mock"
                            or not reservation[5] <= event.occurred_at_ms <= linked_at
                            or _link_hash(
                                "ARK-synthetic-preaction-audit-v1",
                                _audit_identity(event),
                            ) != event_digest
                        ):
                            raise SyntheticRecoveryRejected(
                                "sidecar link audit identity differs"
                            )
                        if request == first.call.request_id:
                            if (
                                (revision, bound)
                                != (first.registry_revision, first.bound_action_id)
                                or (
                                    event.tool, event.capability, event.scope,
                                    event.arguments_sha256,
                                ) != (
                                    call.tool, call.capability, call.scope,
                                    call.arguments_sha256,
                                )
                            ):
                                raise SyntheticRecoveryRejected(
                                    "sidecar link conflicts with registry/action"
                                )
                            pairs.append((occurrence, event_id))
                    link_witness = prefixes[-1]
                    matching_links = tuple(sorted(pairs))
                    assert_epoch()
                    link_conn.commit()
                except BaseException:
                    link_conn.rollback()
                    raise
            assert_epoch()
            # Detect observed audit drift across our independent read phases.
            if review_audit_continuity(
                audit, retained=retained_audit, require_monotonic_time=True,
            ) != audit_witness:
                raise SyntheticRecoveryRejected(
                    "audit history changed during sidecar diagnosis"
                )
        assert_epoch()
        # Independent stores have no shared transaction. Re-observe each
        # local witness after the other reads and reject visible drift.
        # This narrows but cannot eliminate between-read or post-check races.
        if journal.recover(retained=plan.tail) != plan:
            raise SyntheticRecoveryRejected(
                "plan changed during cross-store recovery diagnosis"
            )
        assert_epoch()
        if read_synthetic_ledger_witness(ledger_path) != ledger:
            raise SyntheticRecoveryRejected(
                "reservation history changed during cross-store recovery diagnosis"
            )
        assert_epoch()
        if review_audit_continuity(
            audit, retained=audit_witness, require_monotonic_time=True,
        ) != audit_witness:
            raise SyntheticRecoveryRejected(
                "audit history changed during cross-store recovery diagnosis"
            )
        assert_epoch()
        if link_store is not None and (
            link_witness is None
            or link_store.read_witness(retained=link_witness) != link_witness
        ):
            raise SyntheticRecoveryRejected(
                "link history changed during cross-store recovery diagnosis"
            )
        assert_epoch()
        again = registry.bind(call)
        assert_epoch()
        if (
            again.registry_revision != first.registry_revision
            or again.bound_action_id != first.bound_action_id
            or again.registration is not first.registration
            or again.call is not first.call
        ):
            raise SyntheticRecoveryRejected(
                "registry or action changed during recovery diagnosis"
            )
        return SyntheticRecoveryReview(
            step_id, first.call.request_id, first.registry_revision,
            first.bound_action_id, state[step_id],
            step_id in plan.ambiguous_running_steps,
            plan.tail, ledger, audit_witness, occurrences,
            link_witness, matching_links,
        )
    except (sqlite3.Error, KeyError, TypeError, ValueError, AttributeError) as exc:
        raise SyntheticRecoveryRejected(
            "incomplete or malformed synthetic recovery evidence"
        ) from exc
