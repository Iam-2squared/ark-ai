"""Read-only recheck of a previously retained Planner recovery image.

A later journal event makes a previously reviewed Planner snapshot stale.
Even two matching local reads are not a lock, cross-store transaction, authorization,
independent custody, real-effect proof or permission to replay a WRITE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .planner import _plan_digest
from .planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
    SyntheticPlanRecovery,
    SyntheticPlanTail,
    _require_original_recovery_denials,
)


class PlannerEpochRecheckRejected(ValueError):
    """The detached Planner epoch is not safe to compare."""


_MAX_RECOVERED_STEP_ID_BYTES = 256  # Local review bound; not a Planner v1 limit.


def _valid_recovered_step_id(value: object) -> bool:
    """Bound a detached ID before sorting, hashing, or journal callbacks."""
    if type(value) is not str or not value.strip() or "\x00" in value:
        return False
    try:
        return len(value.encode("utf-8", errors="strict")) <= _MAX_RECOVERED_STEP_ID_BYTES
    except UnicodeError:
        return False


_ORIGINAL_STEP_CHECK = _valid_recovered_step_id


@dataclass(frozen=True, slots=True)
class PlannerEpochRecheck:
    plan_id: str
    retained_event_count: int
    observed_event_count: int
    local_freshness: Literal["MATCH_AT_READ", "DRIFT_AT_READ"]

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
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


_RESULT = PlannerEpochRecheck
_FIELDS = (
    "plan_id", "retained_event_count", "observed_event_count",
    "local_freshness", "__init__", "__new__", "__getattribute__",
    "__getattr__", "dispatch_authorized", "automatic_replay_authorized",
    "freshness_after_return_proven", "external_effect_proven",
    "manual_review_required",
)
_ORIGINAL_FIELDS = tuple(vars(_RESULT).get(name) for name in _FIELDS)
_RECOVER = vars(SyntheticPlanJournal)["recover"]
_STATUS_DIGEST = _plan_digest
# The detached review's own preflight and tail-shape callbacks are mutable
# Python module/class symbols. A substituted callback must not be invoked
# before inspecting retained Planner identities or opening private SQLite.
_ORIGINAL_DENIAL_PRECHECK = _require_original_recovery_denials
_ORIGINAL_TAIL_SHAPE = vars(SyntheticPlanTail)["assert_shape"]


def _originals() -> None:
    if (
        _require_original_recovery_denials is not _ORIGINAL_DENIAL_PRECHECK
        or vars(SyntheticPlanTail).get("assert_shape") is not _ORIGINAL_TAIL_SHAPE
        or _valid_recovered_step_id is not _ORIGINAL_STEP_CHECK
        or type(_MAX_RECOVERED_STEP_ID_BYTES) is not int
        or _MAX_RECOVERED_STEP_ID_BYTES != 256
    ):
        raise PlannerEpochRecheckRejected("Planner recheck reader epoch changed")
    _ORIGINAL_DENIAL_PRECHECK()
    if (
        PlannerEpochRecheck is not _RESULT
        or _plan_digest is not _STATUS_DIGEST
        or vars(SyntheticPlanJournal).get("recover") is not _RECOVER
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_FIELDS, _ORIGINAL_FIELDS, strict=True)
        )
    ):
        raise PlannerEpochRecheckRejected("Planner recheck reader epoch changed")


def _recovery_image(recovered: SyntheticPlanRecovery) -> tuple[object, ...]:
    _originals()
    if type(recovered) is not SyntheticPlanRecovery:
        raise PlannerEpochRecheckRejected("exact Planner recovery required")
    tail = recovered.tail
    if type(tail) is not SyntheticPlanTail:
        raise PlannerEpochRecheckRejected("exact Planner tail required")
    tail.assert_shape()
    statuses = recovered.step_statuses
    running = recovered.ambiguous_running_steps
    if (
        type(statuses) is not tuple or len(statuses) > 24
        or type(running) is not tuple or len(running) > len(statuses)
        or any(
            type(item) is not tuple or len(item) != 3
            or not _valid_recovered_step_id(item[0])
            or type(item[1]) is not str
            or type(item[2]) is not int
            for item in statuses
        )
        or any(not _valid_recovered_step_id(name) for name in running)
        # This is a detached caller-held image, not the journal's own graph.
        # An invalid state, duplicate step, unsorted row or bool revision must
        # never be classified as merely a benign stale Planner snapshot.
        or any(
            not item[0].strip()
            or item[1] not in (
                "pending", "running", "succeeded",
                "failed", "blocked", "cancelled",
            )
            or not 0 <= item[2] <= 2**63 - 1
            for item in statuses
        )
        or tuple(name for name, _, _ in statuses)
        != tuple(sorted({name for name, _, _ in statuses}))
        or running != tuple(
            name for name, state, _ in statuses if state == "running"
        )
        or recovered.dispatch_authorized is not False
        or recovered.automatic_replay_authorized is not False
    ):
        raise PlannerEpochRecheckRejected("Planner image malformed or gained authority")
    # A structurally plausible detached image can still have been edited
    # without updating the canonical status digest bound to its tail. Verify
    # status/tail coherence BEFORE journal access, not as ordinary staleness.
    # The journal's exact PlanGraph.status_digest payload is used here; this
    # is local image integrity, never independently authenticated evidence.
    if any(
        (state == "pending") != (revision == 0)
        for _, state, revision in statuses
    ):
        raise PlannerEpochRecheckRejected("Planner status revision is inconsistent")
    image_epoch = (
        tail.topology_digest, tail.event_count, tail.event_hash,
        tail.status_digest, tail.last_at_ms,
    )
    expected_status_digest = _STATUS_DIGEST(
        "pstate_",
        {
            "schema_version": 1,
            "topology_digest": image_epoch[0],
            "statuses": [
                {"step_id": step_id, "state": state, "revision": revision}
                for step_id, state, revision in statuses
            ],
        },
    )
    _originals()
    if (
        recovered.tail is not tail
        or recovered.step_statuses is not statuses
        or recovered.ambiguous_running_steps is not running
        or (
            tail.topology_digest, tail.event_count, tail.event_hash,
            tail.status_digest, tail.last_at_ms,
        ) != image_epoch
        or expected_status_digest != image_epoch[3]
    ):
        raise PlannerEpochRecheckRejected(
            "Planner detached status digest or carriers changed"
        )
    return (
        tail, statuses, running, *image_epoch,
    )


def recheck_disconnected_planner_epoch(
    journal: SyntheticPlanJournal,
    recovered: SyntheticPlanRecovery,
    retained: SyntheticPlanTail,
) -> PlannerEpochRecheck:
    """Compare retained recovery with two local journal reads; never dispatch.

    The independent earlier tail is replay-checked by the original journal
    reader on each sweep. A commit after the final read may still occur.
    """
    _originals()
    if (
        type(journal) is not SyntheticPlanJournal
        or type(retained) is not SyntheticPlanTail
    ):
        raise PlannerEpochRecheckRejected("exact local Planner inputs required")
    try:
        before = _recovery_image(recovered)
        retained.assert_shape()
        retained_image = (
            retained.topology_digest, retained.event_count, retained.event_hash,
            retained.status_digest, retained.last_at_ms,
        )
        # recover() executes its own isolated SQLite read transaction and
        # checks the retained prefix, but cannot lock another database.
        observed = _RECOVER(journal, retained=retained)
        _originals()
        after = _recovery_image(recovered)
        current = _recovery_image(observed)
        if (
            any(
                old is not new for old, new in zip(
                    before[:3], after[:3], strict=True,
                )
            )
            or before[3:] != after[3:]
            or retained_image != (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            )
            or before[3] != current[3]
        ):
            raise PlannerEpochRecheckRejected("Planner recheck carriers changed")
        local_freshness: Literal["MATCH_AT_READ", "DRIFT_AT_READ"] = (
            "MATCH_AT_READ" if before[3:] == current[3:]
            and before[1] == current[1] and before[2] == current[2]
            else "DRIFT_AT_READ"
        )
        result = _RESULT(
            current[3], before[4], current[4], local_freshness,
        )
        _originals()
        if (
            type(result) is not _RESULT
            or result.dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.freshness_after_return_proven is not False
            or result.external_effect_proven is not False
            or result.manual_review_required is not True
        ):
            raise PlannerEpochRecheckRejected("Planner recheck gained authority")
        # A second original journal sweep catches a local commit that arrived
        # while the first recovery was classified or the denial result was
        # constructed. This is a finite read-only fence, not a durable lease.
        second = _recovery_image(_RECOVER(journal, retained=retained))
        _originals()
        if (
            second[1:] != current[1:]
            or _recovery_image(recovered) != before
            or retained_image != (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            )
            or type(result) is not _RESULT
            or (
                result.plan_id, result.retained_event_count,
                result.observed_event_count, result.local_freshness,
            ) != (current[3], before[4], current[4], local_freshness)
        ):
            raise PlannerEpochRecheckRejected(
                "Planner changed across local recheck sweeps"
            )
        _originals()
        return result
    except (SyntheticPlanJournalRejected, TypeError, AttributeError) as exc:
        raise PlannerEpochRecheckRejected(
            "local Planner epoch cannot be rechecked"
        ) from exc
