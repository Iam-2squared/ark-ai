"""Manual-only cross-store triage of Planner and atomic WRITE snapshots.

Both upstream reviews are locally coherent, but their separate SQLite stores
are NOT atomically coupled. No backend, approval, replay or physical action.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import Effect, PlanStep
from .disconnected_atomic_batch_binding_snapshot_review import (
    AtomicBatchBindingSnapshotReview,
    review_registered_atomic_binding_batch_snapshot,
)
from .disconnected_atomic_binding_snapshot_review import AtomicBindingSnapshotRejected
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
)
from .disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from .disconnected_write_recovery_fence import OfflineRecoveryFence
from .planner_journal_review import SyntheticPlanRecovery
from .registry import ToolRegistry


class RegisteredPlannerAtomicTriageRejected(ValueError):
    """Local sources do not establish a safe recovery correlation."""


@dataclass(frozen=True, slots=True)
class RegisteredPlannerAtomicTriage:
    plan_id: str
    planner_digest: str
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
    def external_effect_proven(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RESULT = RegisteredPlannerAtomicTriage
_PROJECT = project_disconnected_planner_fence
_BATCH = review_registered_atomic_binding_batch_snapshot
_FIELDS = (
    "plan_id", "planner_digest", "retained_atomic_count", "observations",
    "__init__", "__new__", "__getattribute__", "__getattr__",
    "dispatch_authorized", "write_authorized", "automatic_replay_authorized",
    "cross_store_atomicity_proven", "external_effect_proven",
    "manual_review_required",
)
_ORIGINAL_FIELDS = tuple(vars(_RESULT).get(name) for name in _FIELDS)


def _originals() -> None:
    if (
        project_disconnected_planner_fence is not _PROJECT
        or review_registered_atomic_binding_batch_snapshot is not _BATCH
        or RegisteredPlannerAtomicTriage is not _RESULT
        or any(
            vars(_RESULT).get(name) is not old
            for name, old in zip(_FIELDS, _ORIGINAL_FIELDS, strict=True)
        )
    ):
        raise RegisteredPlannerAtomicTriageRejected(
            "manual triage reader or denial definition changed"
        )


def review_registered_planner_atomic_triage(
    recovered: SyntheticPlanRecovery,
    steps: tuple[PlanStep, ...],
    registry: ToolRegistry,
    ledger: DisconnectedAtomicPreactionLedger,
    retained: AtomicPreactionWitness,
    write_occurrences: tuple[tuple[str, str], ...],
) -> RegisteredPlannerAtomicTriage:
    """Correlate all registered WRITE steps; retain every result as manual-only.

    `write_occurrences` contains exact (step_id, occurrence_id) pairs for
    ALL registered WRITEs and no READs. Different-store commits can interleave:
    even LOCAL_MATCH + Planner RUNNING is still an UNKNOWN external effect.
    """
    _originals()
    if (
        type(recovered) is not SyntheticPlanRecovery
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or any(type(step) is not PlanStep for step in steps)
        or type(registry) is not ToolRegistry
        or type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(retained) is not AtomicPreactionWitness
        or type(write_occurrences) is not tuple
        or not 1 <= len(write_occurrences) <= len(steps)
    ):
        raise RegisteredPlannerAtomicTriageRejected(
            "exact bounded triage inputs required"
        )
    # The WRITE occurrence tuple is independent caller input, not a registry
    # identity. Refuse malformed and oversized entries *before* reading any
    # Planner/registry/SQLite witness or calling a registry resolver. This
    # prevents an invalid manual-recovery request from reaching callbacks.
    names_seen: set[str] = set()
    occurrences_seen: set[str] = set()
    for pair in write_occurrences:
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or type(pair[1]) is not str
            or not pair[0].strip() or len(pair[0]) > 256
            or len(pair[1]) != 68 or not pair[1].startswith("occ_")
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "malformed bounded WRITE occurrence before review"
            )
        try:
            encoded_name = pair[0].encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise RegisteredPlannerAtomicTriageRejected(
                "invalid UTF-8 WRITE step identity"
            ) from exc
        if (
            len(encoded_name) > 256
            or re.fullmatch(r"occ_[0-9a-f]{64}", pair[1]) is None
            or pair[0] in names_seen or pair[1] in occurrences_seen
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "invalid or repeated WRITE occurrence before review"
            )
        names_seen.add(pair[0])
        occurrences_seen.add(pair[1])
    if (
        type(retained.count) is not int or not 0 <= retained.count <= 128
        or type(retained.tip_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", retained.tip_sha256) is None
    ):
        raise RegisteredPlannerAtomicTriageRejected(
            "invalid retained atomic witness before review"
        )
    originals = tuple(
        (s, s.step_id, s.call, s.depends_on, s.call.tool, s.call.capability,
         s.call.scope, s.call.arguments, s.call.request_id)
        for s in steps
    )
    recovery_image = (
        recovered.tail, recovered.step_statuses, recovered.ambiguous_running_steps,
    )
    retained_image = (retained.count, retained.tip_sha256)

    def stable() -> None:
        _originals()
        if (
            any(now is not old for now, old in zip(
                (recovered.tail, recovered.step_statuses,
                 recovered.ambiguous_running_steps), recovery_image, strict=True,
            ))
            or retained.count is not retained_image[0]
            or retained.tip_sha256 is not retained_image[1]
            or any(
                s is not old or s.step_id is not name or s.call is not call
                or s.depends_on is not deps or call.tool is not tool
                or call.capability is not cap or call.scope is not scope
                or call.arguments is not args or call.request_id != request
                for s, (old, name, call, deps, tool, cap, scope, args, request)
                in zip(steps, originals, strict=True)
            )
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "triage source changed across read boundaries"
            )

    stable()
    try:
        effects = tuple(
            (step.step_id, registry.resolve(step.call).effect) for step in steps
        )
        stable()
        if (
            len(set(name for name, _ in effects)) != len(steps)
            or any(type(effect) is not Effect for _, effect in effects)
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "unregistered, duplicate or malformed Planner step"
            )
        effect_map = dict(effects)
        writes = {name for name, effect in effects if effect is Effect.WRITE}
        bindings: dict[str, str] = {}
        occurrence_ids: set[str] = set()
        for pair in write_occurrences:
            if (
                type(pair) is not tuple or len(pair) != 2
                or type(pair[0]) is not str or type(pair[1]) is not str
                or re.fullmatch(r"occ_[0-9a-f]{64}", pair[1]) is None
                or pair[0] not in writes or pair[0] in bindings
                or pair[1] in occurrence_ids
            ):
                raise RegisteredPlannerAtomicTriageRejected(
                    "invalid, duplicate or READ-bound occurrence"
                )
            bindings[pair[0]] = pair[1]
            occurrence_ids.add(pair[1])
        if set(bindings) != writes:
            raise RegisteredPlannerAtomicTriageRejected(
                "missing registered WRITE occurrence"
            )
        fence = _PROJECT(
            recovered, steps, tuple((name, effect.name) for name, effect in effects),
        )
        stable()
        if (
            type(fence) is not OfflineRecoveryFence
            or fence.dispatch_authorized is not False
            or fence.write_authorized is not False
            or fence.automatic_replay_authorized is not False
            or fence.external_outcome_verified is not False
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "Planner fence gained authority"
            )
        call_map = {step.step_id: step.call for step in steps}
        requested = tuple((bindings[name], call_map[name]) for name in sorted(writes))
        batch = _BATCH(ledger, retained, registry, requested)
        stable()
        if (
            type(batch) is not AtomicBatchBindingSnapshotReview
            or batch.tool_dispatch_authorized is not False
            or batch.automatic_replay_authorized is not False
            or batch.external_effect_proven is not False
            or batch.independently_authenticated is not False
            or batch.manual_review_required is not True
            or batch.retained_count != retained_image[0]
            or type(batch.local_states) is not tuple
            or len(batch.local_states) != len(requested)
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "atomic review gained authority"
            )
        local = dict(batch.local_states)
        codes = {item.step_id: item.code for item in fence.decisions}
        if (
            len(local) != len(requested) or set(local) != occurrence_ids
            or any(state not in ("ABSENT", "LOCAL_MATCH", "LOCAL_CONFLICT")
                   for state in local.values())
            or len(codes) != len(steps) or set(codes) != set(effect_map)
        ):
            raise RegisteredPlannerAtomicTriageRejected("triage membership differs")
        result = _RESULT(
            fence.plan_id, fence.digest, batch.retained_count,
            tuple(
                (step.step_id, effect_map[step.step_id].name, codes[step.step_id],
                 local[bindings[step.step_id]]
                 if step.step_id in writes else "NOT_APPLICABLE")
                for step in steps
            ),
        )
        stable()
        if (
            type(result) is not _RESULT
            or result.dispatch_authorized is not False
            or result.write_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.cross_store_atomicity_proven is not False
            or result.external_effect_proven is not False
            or result.manual_review_required is not True
        ):
            raise RegisteredPlannerAtomicTriageRejected(
                "triage result gained authority"
            )
        return result
    except (
        AtomicBindingSnapshotRejected, DisconnectedPlannerProjectionRejected,
        KeyError, TypeError, ValueError,
    ) as exc:
        if type(exc) is RegisteredPlannerAtomicTriageRejected:
            raise
        raise RegisteredPlannerAtomicTriageRejected(
            "registered Planner/atomic local review rejected"
        ) from exc
