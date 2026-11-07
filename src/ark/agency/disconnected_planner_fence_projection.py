"""Conservative, read-only projection from synthetic Planner recovery to a fence.

This *never* validates the SQLite journal, a registry effect, a permission,
human consent, an external result or an execution clock. A caller must first
recover its own retained journal witness. Effects are explicit untrusted
fixture labels, not a ToolRegistry resolution. No backend is called.

Without a separately reviewed result receipt there is no safe way to label
a recovered SUCCEEDED step as COMPLETE_UNVERIFIED without fabricating a hash.
Accordingly this adapter refuses SUCCEEDED rather than inventing a receipt.
"""

from __future__ import annotations

from . import disconnected_write_recovery_fence as fence_module
from . import planner_journal_review as journal
from .contracts import PlanStep
from .disconnected_write_recovery_fence import (
    OfflineRecoveryFence,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)
from .planner import PlanGraph, _plan_digest


class DisconnectedPlannerProjectionRejected(ValueError):
    """Synthetic recovery cannot be mapped to a non-authorizing exact fence."""


_JOURNAL_RESULT = journal.SyntheticPlanRecovery
_JOURNAL_TAIL = journal.SyntheticPlanTail
_ORIGINAL_TAIL_SHAPE = vars(_JOURNAL_TAIL)["assert_shape"]
# An injected projection-level callback or replaced class descriptor must not
# turn an otherwise sound local journal into an unrelated detached fence.
_ORIGINAL_FENCE_REVIEW = review_disconnected_recovery_fence


def _require_original_fence_review() -> None:
    if (
        review_disconnected_recovery_fence is not _ORIGINAL_FENCE_REVIEW
        or fence_module.review_disconnected_recovery_fence is not _ORIGINAL_FENCE_REVIEW
        or fence_module.OfflineRecoveryFence is not OfflineRecoveryFence
        or fence_module.OfflineRecoveryStepClaim is not OfflineRecoveryStepClaim
    ):
        raise DisconnectedPlannerProjectionRejected(
            "detached recovery fence review authority changed"
        )
    try:
        fence_module._require_original_fence_denials()
    except fence_module.OfflineRecoveryFenceRejected as exc:
        raise DisconnectedPlannerProjectionRejected(
            "detached recovery fence carrier authority changed"
        ) from exc


def project_disconnected_planner_fence(
    recovered: journal.SyntheticPlanRecovery,
    steps: tuple[PlanStep, ...],
    effects: tuple[tuple[str, str], ...],
) -> OfflineRecoveryFence:
    """Build a deterministic READ/WRITE hold view, never a dispatch permit.

    Every source status and effect label remains a local, caller-supplied
    claim. RUNNING is represented as UNKNOWN across restart. SUCCEEDED
    requires an independent reviewed receipt bridge and is rejected here.
    """
    journal._require_original_recovery_denials()
    _require_original_fence_review()
    if (
        type(recovered) is not _JOURNAL_RESULT
        or type(recovered.tail) is not _JOURNAL_TAIL
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or any(type(step) is not PlanStep for step in steps)
        or type(effects) is not tuple or len(effects) != len(steps)
        or vars(_JOURNAL_TAIL).get("assert_shape") is not _ORIGINAL_TAIL_SHAPE
    ):
        raise DisconnectedPlannerProjectionRejected("exact detached projection inputs required")
    tail = recovered.tail
    tail_epoch = (
        tail.topology_digest, tail.event_count, tail.event_hash,
        tail.status_digest, tail.last_at_ms,
    )
    statuses = recovered.step_statuses
    ambiguous = recovered.ambiguous_running_steps
    if type(statuses) is not tuple or type(ambiguous) is not tuple:
        raise DisconnectedPlannerProjectionRejected("malformed Planner status snapshot")
    # A frozen ToolCall is reflectively mutable. Pin nested exact carriers,
    # not only PlanStep.call identity: a callback may retarget its tool/scope
    # or substitute value-equal arguments after the topology was hashed.
    original_steps = tuple(
        (
            step, step.step_id, step.call, step.depends_on,
            step.call.tool, step.call.capability, step.call.scope,
            step.call.arguments, step.call.request_id,
        )
        for step in steps
    )
    original_effects = effects

    def stable() -> None:
        journal._require_original_recovery_denials()
        _require_original_fence_review()
        if (
            vars(_JOURNAL_TAIL).get("assert_shape") is not _ORIGINAL_TAIL_SHAPE
            or type(recovered) is not _JOURNAL_RESULT
            or recovered.tail is not tail
            or recovered.step_statuses is not statuses
            or recovered.ambiguous_running_steps is not ambiguous
            or not journal._retained_tail_epoch_stable(tail, tail_epoch)
            or effects is not original_effects
            or any(
                step is not old or step.step_id is not name
                or step.call is not call or step.depends_on is not deps
                or call.tool is not tool
                or call.capability is not capability
                or call.scope is not scope
                or call.arguments is not arguments
                or call.request_id != request_id
                for step, (
                    old, name, call, deps, tool, capability, scope,
                    arguments, request_id,
                ) in zip(steps, original_steps, strict=True)
            )
        ):
            raise DisconnectedPlannerProjectionRejected("projection inputs changed")

    stable()
    try:
        _ORIGINAL_TAIL_SHAPE(tail)
        graph = PlanGraph(steps)
        identity = graph.topology_digest()
    except (TypeError, ValueError, RuntimeError) as exc:
        raise DisconnectedPlannerProjectionRejected(
            "Planner topology or retained tail rejected"
        ) from exc
    stable()
    if identity != tail_epoch[0]:
        raise DisconnectedPlannerProjectionRejected("Planner topology differs from journal")

    effect_map: dict[str, str] = {}
    for item in effects:
        if (
            type(item) is not tuple or len(item) != 2
            or type(item[0]) is not str or type(item[1]) is not str
            or item[1] not in ("READ", "WRITE")
            or item[0] in effect_map
        ):
            raise DisconnectedPlannerProjectionRejected("invalid exact effect labels")
        effect_map[item[0]] = item[1]
    dependencies = {step.step_id: step.depends_on for step in steps}
    if set(effect_map) != set(dependencies):
        raise DisconnectedPlannerProjectionRejected("effect labels do not match topology")

    states: dict[str, str] = {}
    revisions: dict[str, int] = {}
    for entry in statuses:
        if (
            type(entry) is not tuple or len(entry) != 3
            or type(entry[0]) is not str or entry[0] in states
            or type(entry[1]) is not str
            or entry[1] not in (
                "pending", "running", "failed", "cancelled", "blocked",
            )
            or type(entry[2]) is not int
            or not 0 <= entry[2] <= (1 << 63) - 1
        ):
            raise DisconnectedPlannerProjectionRejected(
                "unsupported, unverified or malformed recovery status"
            )
        states[entry[0]] = entry[1]
        revisions[entry[0]] = entry[2]
    if set(states) != set(dependencies) or ambiguous != tuple(
        name for name in sorted(states) if states[name] == "running"
    ):
        raise DisconnectedPlannerProjectionRejected(
            "recovery status membership or ambiguous RUNNING drift"
        )

    # A caller can replace a frozen SyntheticPlanRecovery's status tuple
    # without changing the separately retained tail. Verify the *entire*
    # recovered status image against the replay tail before projecting any
    # READY_MOCK_ONLY code. This is local consistency, not writer attestation.
    observed_status_digest = _plan_digest(
        "pstate_",
        {
            "schema_version": 1,
            "topology_digest": identity,
            "statuses": [
                {"step_id": name, "state": states[name], "revision": revisions[name]}
                for name in sorted(states)
            ],
        },
    )
    stable()
    if observed_status_digest != tail_epoch[3]:
        raise DisconnectedPlannerProjectionRejected(
            "recovered Planner statuses differ from retained tail digest"
        )

    # Reorder caller-provided steps into the fence's canonical dependency-first
    # order. This is not a scheduler and does not make any step executable.
    remaining = set(states)
    ordered: list[str] = []
    while remaining:
        available = sorted(
            name for name in remaining if set(dependencies[name]) <= set(ordered)
        )
        if not available:
            raise DisconnectedPlannerProjectionRejected("recovery topology is not a DAG")
        selected = available[0]
        remaining.remove(selected)
        ordered.append(selected)

    claims = tuple(
        OfflineRecoveryStepClaim(
            name,
            effect_map[name],
            tuple(sorted(dependencies[name])),
            "UNKNOWN" if states[name] == "running" else states[name].upper(),
        )
        for name in ordered
    )
    stable()
    try:
        fence = review_disconnected_recovery_fence(identity, claims)
    except ValueError as exc:
        raise DisconnectedPlannerProjectionRejected(
            "disconnected recovery fence rejected projected claims"
        ) from exc
    stable()
    if (
        type(fence) is not OfflineRecoveryFence
        or fence.plan_id is not identity
        or type(fence.decisions) is not tuple
        or len(fence.decisions) != len(ordered)
        or tuple(decision.step_id for decision in fence.decisions) != tuple(ordered)
        or type(fence.digest) is not str
        or fence.dispatch_authorized is not False
        or fence.write_authorized is not False
        or fence.automatic_replay_authorized is not False
        or fence.external_outcome_verified is not False
    ):
        raise DisconnectedPlannerProjectionRejected("projection is not an inert fence")
    stable()
    return fence
