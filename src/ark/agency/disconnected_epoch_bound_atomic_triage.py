"""Optional fresh-at-read Planner gate for inert cross-store atomic triage.

This is a two-read, separate-database diagnostic only. A matching Planner
journal before AND after atomic review is not an atomic transaction, durable
lease, trusted consent, proof of external execution, or permission to retry.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import PlanStep
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionSnapshot,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
)
from .disconnected_planner_epoch_recheck import (
    PlannerEpochRecheck,
    PlannerEpochRecheckRejected,
    recheck_disconnected_planner_epoch,
)
from .disconnected_registered_planner_atomic_triage import (
    RegisteredPlannerAtomicTriage,
    RegisteredPlannerAtomicTriageRejected,
    review_registered_planner_atomic_triage,
)
from .planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanRecovery,
    SyntheticPlanTail,
)
from .registry import ToolRegistry


class EpochBoundAtomicTriageRejected(ValueError):
    """Refuse a stale, malformed, or authority-bearing manual review."""


@dataclass(frozen=True, slots=True)
class EpochBoundAtomicTriage:
    plan_id: str
    planner_event_count: int
    retained_atomic_count: int
    observations: tuple[tuple[str, str, str, str], ...]

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def freshness_after_return_proven(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RECHECK = recheck_disconnected_planner_epoch
_TRIAGE = review_registered_planner_atomic_triage
_RESULT = EpochBoundAtomicTriage
_INSPECT = vars(DisconnectedAtomicPreactionLedger)["inspect"]
_MEMBERS = (
    "plan_id", "planner_event_count", "retained_atomic_count",
    "observations", "__init__", "__new__", "__getattribute__", "__getattr__",
    "dispatch_authorized", "write_authorized", "automatic_replay_authorized",
    "cross_store_atomicity_proven", "freshness_after_return_proven",
    "external_effect_proven", "manual_review_required",
)
_ORIGINAL_MEMBERS = tuple(vars(_RESULT).get(name) for name in _MEMBERS)


def _originals() -> None:
    if (
        recheck_disconnected_planner_epoch is not _RECHECK
        or review_registered_planner_atomic_triage is not _TRIAGE
        or EpochBoundAtomicTriage is not _RESULT
        or vars(DisconnectedAtomicPreactionLedger).get("inspect") is not _INSPECT
        or _checked_epoch is not _CHECKED_EPOCH
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_MEMBERS, _ORIGINAL_MEMBERS, strict=True)
        )
    ):
        raise EpochBoundAtomicTriageRejected(
            "manual Planner/atomic triage reader definition changed"
        )


def _checked_epoch(
    journal: SyntheticPlanJournal,
    recovered: SyntheticPlanRecovery,
    retained_planner: SyntheticPlanTail,
) -> PlannerEpochRecheck:
    _originals()
    epoch = _RECHECK(journal, recovered, retained_planner)
    _originals()
    if (
        type(epoch) is not PlannerEpochRecheck
        or epoch.dispatch_authorized is not False
        or epoch.automatic_replay_authorized is not False
        or epoch.freshness_after_return_proven is not False
        or epoch.external_effect_proven is not False
        or epoch.manual_review_required is not True
        or type(epoch.plan_id) is not str
        or type(epoch.retained_event_count) is not int
        or type(epoch.observed_event_count) is not int
        or epoch.local_freshness != "MATCH_AT_READ"
        or epoch.retained_event_count != epoch.observed_event_count
    ):
        raise EpochBoundAtomicTriageRejected(
            "Planner image drifted or recheck gained authority"
        )
    return epoch


_CHECKED_EPOCH = _checked_epoch


def review_epoch_bound_atomic_triage(
    journal: SyntheticPlanJournal,
    recovered: SyntheticPlanRecovery,
    retained_planner: SyntheticPlanTail,
    steps: tuple[PlanStep, ...],
    registry: ToolRegistry,
    ledger: DisconnectedAtomicPreactionLedger,
    retained_atomic: AtomicPreactionWitness,
    write_occurrences: tuple[tuple[str, str], ...],
) -> EpochBoundAtomicTriage:
    """Read Planner -> atomic -> Planner, rejecting any observed Planner drift.

    Two Planner reads can detect some intervening writes but cannot prevent a
    COMMIT after the second read; separate SQLite databases are never locked
    together. This function has no backend, reservation, or approval path.
    """
    _originals()
    if (
        type(journal) is not SyntheticPlanJournal
        or type(recovered) is not SyntheticPlanRecovery
        or type(retained_planner) is not SyntheticPlanTail
        or type(steps) is not tuple
        or type(registry) is not ToolRegistry
        or type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(retained_atomic) is not AtomicPreactionWitness
        or type(write_occurrences) is not tuple
    ):
        raise EpochBoundAtomicTriageRejected("exact inert inputs required")
    # Two SQLite snapshots cannot atomically freeze the caller's detached
    # Planner recovery objects. Keep their exact carrier/field epoch across
    # the independent atomic callback and the result-construction boundary.
    recovery_tail = recovered.tail
    recovery_epoch = (
        recovered.tail, recovered.step_statuses,
        recovered.ambiguous_running_steps,
    )
    tail_epoch = (
        recovery_tail.topology_digest, recovery_tail.event_count,
        recovery_tail.event_hash, recovery_tail.status_digest,
        recovery_tail.last_at_ms,
    )
    retained_epoch = (
        retained_planner.topology_digest, retained_planner.event_count,
        retained_planner.event_hash, retained_planner.status_digest,
        retained_planner.last_at_ms,
    )

    def stable_planner_inputs() -> None:
        _originals()
        if (
            type(recovered) is not SyntheticPlanRecovery
            or type(retained_planner) is not SyntheticPlanTail
            or type(recovered.tail) is not SyntheticPlanTail
            or any(current is not original for current, original in zip(
                (recovered.tail, recovered.step_statuses,
                 recovered.ambiguous_running_steps),
                recovery_epoch, strict=True,
            ))
            or any(current is not original for current, original in zip(
                (recovery_tail.topology_digest, recovery_tail.event_count,
                 recovery_tail.event_hash, recovery_tail.status_digest,
                 recovery_tail.last_at_ms),
                tail_epoch, strict=True,
            ))
            or any(current is not original for current, original in zip(
                (retained_planner.topology_digest, retained_planner.event_count,
                 retained_planner.event_hash, retained_planner.status_digest,
                 retained_planner.last_at_ms),
                retained_epoch, strict=True,
            ))
        ):
            raise EpochBoundAtomicTriageRejected(
                "Planner recovery input epoch changed during cross-store review"
            )

    stable_planner_inputs()
    try:
        first = _checked_epoch(journal, recovered, retained_planner)
        stable_planner_inputs()
        triage = _TRIAGE(
            recovered, steps, registry, ledger, retained_atomic,
            write_occurrences,
        )
        _originals()
        if (
            type(triage) is not RegisteredPlannerAtomicTriage
            or triage.dispatch_authorized is not False
            or triage.write_authorized is not False
            or triage.automatic_replay_authorized is not False
            or triage.cross_store_atomicity_proven is not False
            or triage.external_effect_proven is not False
            or triage.manual_review_required is not True
            or triage.plan_id != first.plan_id
            or type(triage.retained_atomic_count) is not int
            or type(triage.observations) is not tuple
        ):
            raise EpochBoundAtomicTriageRejected(
                "atomic cross-store triage lost its manual-only fence"
            )
        stable_planner_inputs()
        triage_epoch = (triage.plan_id, triage.retained_atomic_count, triage.observations)
        second = _checked_epoch(journal, recovered, retained_planner)
        stable_planner_inputs()
        # The atomic review and Planner recheck are separate SQLite reads.
        # A second atomic snapshot detects a new reservation committed while
        # Planner was being rechecked; it does not lock either database.
        atomic_after = _INSPECT(ledger, retained_atomic)
        _originals()
        if (
            type(atomic_after) is not AtomicPreactionSnapshot
            or type(atomic_after.witness) is not AtomicPreactionWitness
            or type(atomic_after.witness.count) is not int
            or type(atomic_after.witness.tip_sha256) is not str
            or type(retained_atomic.count) is not int
            or type(retained_atomic.tip_sha256) is not str
            or atomic_after.witness.count != triage.retained_atomic_count
            or atomic_after.witness.count != retained_atomic.count
            or atomic_after.witness.tip_sha256 != retained_atomic.tip_sha256
            or type(atomic_after.occurrence_ids) is not tuple
            or len(atomic_after.occurrence_ids) != atomic_after.witness.count
        ):
            raise EpochBoundAtomicTriageRejected(
                "atomic history drifted across Planner recheck"
            )
        if (
            second.plan_id != first.plan_id
            or second.observed_event_count != first.observed_event_count
            or second.retained_event_count != first.retained_event_count
            or recovered.tail.event_count != first.observed_event_count
        ):
            raise EpochBoundAtomicTriageRejected(
                "Planner changed across atomic review"
            )
        stable_planner_inputs()
        if any(current is not original for current, original in zip(
            (triage.plan_id, triage.retained_atomic_count, triage.observations),
            triage_epoch, strict=True,
        )):
            raise EpochBoundAtomicTriageRejected(
                "atomic child receipt changed during Planner recheck"
            )
        result = _RESULT(
            first.plan_id, second.observed_event_count,
            triage_epoch[1], triage_epoch[2],
        )
        stable_planner_inputs()
        if (
            type(result) is not _RESULT
            or result.dispatch_authorized is not False
            or result.write_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.cross_store_atomicity_proven is not False
            or result.freshness_after_return_proven is not False
            or result.external_effect_proven is not False
            or result.manual_review_required is not True
        ):
            raise EpochBoundAtomicTriageRejected("result gained authority")
        stable_planner_inputs()
        return result
    except (
        PlannerEpochRecheckRejected, RegisteredPlannerAtomicTriageRejected,
        AtomicPreactionRejected,
        TypeError, AttributeError,
    ) as exc:
        raise EpochBoundAtomicTriageRejected(
            "epoch-bound manual triage rejected"
        ) from exc
