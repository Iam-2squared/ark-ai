"""Read-only, disconnected cross-store recovery diagnosis for synthetic WRITE.

This review observes three independently committed SQLite stores. It is NOT
a cross-store transaction, external action receipt, authorization, or replay
instruction. A reservation and an audit event can never prove side effects.
All clocks, registrations, and retained witnesses are caller supplied.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
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
from .synthetic_occurrence_continuity_review import (
    _COLUMNS,
    SyntheticLedgerWitness,
    _digest,
    assert_synthetic_history_continues,
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
    ):
        raise SyntheticRecoveryRejected("retained witnesses must use exact types")

    try:
        first = registry.bind(call)
        if first.registration.effect is not Effect.WRITE:
            raise SyntheticRecoveryRejected("only WRITE fixtures may be reviewed")
        # The journal's persisted topology is checked by recover(). Do not
        # infer an identity match from a step name alone.
        topology = PlanGraph(journal._steps)
        if step_id not in topology.steps:
            raise SyntheticRecoveryRejected("step is not in the plan topology")
        if topology.steps[step_id].call.request_id != first.call.request_id:
            raise SyntheticRecoveryRejected("plan step action identity differs")
        plan = journal.recover(retained=retained_plan)
        state = dict((name, value) for name, value, _ in plan.step_statuses)
        if step_id not in state:
            raise SyntheticRecoveryRejected("step is missing from recovery")
        # Ledger identities and their witness MUST be collected from the SAME
        # read transaction. A separate earlier/later witness would be racy.
        uri = ledger_path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
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
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        audit_witness = review_audit_continuity(
            audit, retained=retained_audit, require_monotonic_time=True,
        )
        again = registry.bind(call)
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
        )
    except (sqlite3.Error, KeyError, TypeError, ValueError, AttributeError) as exc:
        raise SyntheticRecoveryRejected(
            "incomplete or malformed synthetic recovery evidence"
        ) from exc
