"""Optional fresh-at-read Planner gate for inert cross-store atomic triage.

This is a two-read, separate-database diagnostic only. A matching Planner
journal before AND after atomic review is not an atomic transaction, durable
lease, trusted consent, proof of external execution, or permission to retry.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import PlanStep
from .disconnected_atomic_preaction_ledger import (
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
    try:
        first = _checked_epoch(journal, recovered, retained_planner)
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
        second = _checked_epoch(journal, recovered, retained_planner)
        if (
            second.plan_id != first.plan_id
            or second.observed_event_count != first.observed_event_count
            or second.retained_event_count != first.retained_event_count
            or recovered.tail.event_count != first.observed_event_count
        ):
            raise EpochBoundAtomicTriageRejected(
                "Planner changed across atomic review"
            )
        result = _RESULT(
            first.plan_id, second.observed_event_count,
            triage.retained_atomic_count, triage.observations,
        )
        _originals()
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
        return result
    except (
        PlannerEpochRecheckRejected, RegisteredPlannerAtomicTriageRejected,
        TypeError, AttributeError,
    ) as exc:
        raise EpochBoundAtomicTriageRejected(
            "epoch-bound manual triage rejected"
        ) from exc
