"""Read-only join of a recovered Planner journal and WRITE-ancestry holds.

A synthetic recovery can say RUNNING/UNKNOWN while its independent DAG
review says HOLD. This joins both *without* treating either as authorization,
authenticated provenance, an atomic cross-store snapshot or a retry permit.
The caller owns both inputs; their local digest is not a trusted signature.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from heapq import heappop, heappush

from .contracts import Effect, StepState
from .disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyHold,
    DisconnectedDependencyProjection,
)
from .planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail

_MAX_STEPS = 128
_MAX_EDGES = 4096
_MAX_REVISION = (1 << 63) - 1
_DOMAIN = b"ARK-disconnected-restart-dependency-join-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class DisconnectedRestartDependencyRejected(ValueError):
    """Synthetic journal and hold projections cannot be joined safely."""


@dataclass(frozen=True, slots=True)
class RestartDependencyHold:
    step_id: str
    recovered_state: str
    reason: str
    outcome_unknown: bool


@dataclass(frozen=True, slots=True)
class RestartDependencyReview:
    topology_digest: str
    plan_event_hash: str
    quarantine_digest: str
    holds: tuple[RestartDependencyHold, ...]
    uncertain_step_ids: tuple[str, ...]
    review_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def trusted_provenance_verified(self) -> bool:
        return False


_RECOVERY = SyntheticPlanRecovery
_TAIL = SyntheticPlanTail
_PROJECTION = DisconnectedDependencyProjection
_CLAIM = DisconnectedDependencyClaim
_HOLD = DisconnectedDependencyHold
_RESULT = RestartDependencyReview
_ORIGINAL_PROTOCOL = (_MAX_STEPS, _MAX_EDGES, _MAX_REVISION, _DOMAIN, _SHA)
_ORIGINAL_DEPENDENCIES = (hashlib.sha256, json.dumps, heappush, heappop)
_ORIGINAL_DENIALS = {
    _RECOVERY: ("dispatch_authorized", "automatic_replay_authorized"),
    _PROJECTION: (
        "dispatch_authorized", "automatic_replay_authorized",
        "external_outcome_verified", "independent_custody_proven",
    ),
    _RESULT: (
        "dispatch_authorized", "automatic_replay_authorized",
        "external_outcome_verified", "trusted_provenance_verified",
    ),
}
_ORIGINAL_PROPERTIES = tuple(
    (cls, name, vars(cls).get(name))
    for cls, names in _ORIGINAL_DENIALS.items() for name in names
)
_ORIGINAL_SLOTS = tuple(
    (cls, name, vars(cls).get(name))
    for cls, names in (
        (_RECOVERY, ("tail", "step_statuses", "ambiguous_running_steps")),
        (_TAIL, (
            "topology_digest", "event_count", "event_hash",
            "status_digest", "last_at_ms",
        )),
        (_PROJECTION, ("topology_digest", "matrix_digest", "holds", "digest")),
        (_CLAIM, ("step_id", "effect", "state", "depends_on")),
        (_HOLD, ("step_id", "reason")),
        (_RESULT, (
            "topology_digest", "plan_event_hash", "quarantine_digest",
            "holds", "uncertain_step_ids", "review_sha256",
        )),
    ) for name in names
)


def _require_original_contract() -> None:
    if (
        type(_MAX_STEPS) is not int or type(_MAX_EDGES) is not int
        or type(_MAX_REVISION) is not int
        or (_MAX_STEPS, _MAX_EDGES, _MAX_REVISION, _DOMAIN, _SHA)
        != _ORIGINAL_PROTOCOL
        or (hashlib.sha256, json.dumps, heappush, heappop)
        != _ORIGINAL_DEPENDENCIES
        or any(vars(cls).get(name) is not descriptor
               for cls, name, descriptor in _ORIGINAL_PROPERTIES + _ORIGINAL_SLOTS)
        or any(
            vars(cls).get(name) is not old
            for cls, name, old in (
                (_RECOVERY, "__getattribute__", object.__getattribute__),
                (_CLAIM, "__getattribute__", object.__getattribute__),
            )
            if vars(cls).get(name) is not None
        )
    ):
        raise DisconnectedRestartDependencyRejected("restart join protocol changed")


def _identity(value: object) -> bool:
    if type(value) is not str or not value.strip() or len(value) > 256:
        return False
    try:
        return "\x00" not in value and len(value.encode("utf-8", "strict")) <= 256
    except UnicodeError:
        return False


def review_disconnected_restart_dependency(
    *,
    recovered: SyntheticPlanRecovery,
    dependency: DisconnectedDependencyProjection,
    claims: tuple[DisconnectedDependencyClaim, ...],
    retained_tail: SyntheticPlanTail,
) -> RestartDependencyReview:
    """Join independently retained journal and DAG facts; always HOLD.

    The retained tail is caller-controlled. Its equality is an epoch check,
    NOT proof that the journal was independently authenticated.
    """
    _require_original_contract()
    if (
        type(recovered) is not _RECOVERY
        or type(recovered.tail) is not _TAIL
        or type(dependency) is not _PROJECTION
        or type(retained_tail) is not _TAIL
        or type(claims) is not tuple or not 1 <= len(claims) <= _MAX_STEPS
        or type(recovered.step_statuses) is not tuple
        or len(recovered.step_statuses) != len(claims)
        or type(recovered.ambiguous_running_steps) is not tuple
        or type(dependency.holds) is not tuple
        or len(dependency.holds) != len(claims)
    ):
        raise DisconnectedRestartDependencyRejected("restart input type or budget mismatch")

    try:
        retained_tail.assert_shape()
        recovered.tail.assert_shape()
    except (ValueError, TypeError, AttributeError) as exc:
        raise DisconnectedRestartDependencyRejected("retained journal tail invalid") from exc

    tail_fields = (
        "topology_digest", "event_count", "event_hash", "status_digest", "last_at_ms",
    )
    retained = tuple(getattr(retained_tail, name) for name in tail_fields)
    observed = tuple(getattr(recovered.tail, name) for name in tail_fields)
    if observed != retained or (
        dependency.topology_digest != observed[0]
        or type(dependency.digest) is not str
        or _SHA.fullmatch(dependency.digest) is None
        or type(dependency.matrix_digest) is not str
        or len(dependency.matrix_digest) > 128
    ):
        raise DisconnectedRestartDependencyRejected("journal/quarantine epoch mismatch")

    for source, properties in (
        (recovered, _ORIGINAL_DENIALS[_RECOVERY]),
        (dependency, _ORIGINAL_DENIALS[_PROJECTION]),
    ):
        _require_original_contract()
        if any(getattr(source, name) is not False for name in properties):
            raise DisconnectedRestartDependencyRejected("source gained execution authority")

    names: list[str] = []
    pinned_claims = []
    for item in claims:
        _require_original_contract()
        if type(item) is not _CLAIM:
            raise DisconnectedRestartDependencyRejected("inexact dependency claim")
        row = (item.step_id, item.effect, item.state, item.depends_on)
        if (
            not _identity(row[0]) or type(row[1]) is not Effect
            or type(row[2]) is not StepState or type(row[3]) is not tuple
            or len(row[3]) > _MAX_STEPS
            or row[3] != tuple(sorted(set(row[3])))
            or any(not _identity(parent) for parent in row[3])
            or row[0] in row[3]
        ):
            raise DisconnectedRestartDependencyRejected("invalid dependency topology")
        pinned_claims.append((item, row))
        names.append(row[0])
    if names != sorted(set(names)):
        raise DisconnectedRestartDependencyRejected("incomplete or unsorted dependency claims")

    statuses = recovered.step_statuses
    pinned_statuses = []
    for name, status in zip(names, statuses, strict=True):
        if (
            type(status) is not tuple or len(status) != 3
            or type(status[0]) is not str or status[0] != name
            or type(status[1]) is not str
            or status[1] not in {state.value for state in StepState}
            or type(status[2]) is not int
            or not 0 <= status[2] <= _MAX_REVISION
        ):
            raise DisconnectedRestartDependencyRejected("recovered status mismatch")
        pinned_statuses.append(status)
    expected_running = tuple(
        name for name, state, _ in pinned_statuses if state == StepState.RUNNING.value
    )
    if (
        recovered.ambiguous_running_steps != expected_running
        or any(
            claim.state.value != status[1]
            for (_, claim), status in zip(pinned_claims, pinned_statuses, strict=True)
        )
    ):
        raise DisconnectedRestartDependencyRejected("RUNNING/UNKNOWN or state mismatch")

    index = {row[0]: row for _, row in pinned_claims}
    edge_count = sum(len(row[3]) for _, row in pinned_claims)
    if edge_count > _MAX_EDGES:
        raise DisconnectedRestartDependencyRejected("dependency edge budget")
    children = {name: [] for name in names}
    indegree = {name: len(row[3]) for name, row in index.items()}
    for name, row in index.items():
        for parent in row[3]:
            if parent not in index:
                raise DisconnectedRestartDependencyRejected("missing dependency")
            children[parent].append(name)
    ready = []
    for name in names:
        if indegree[name] == 0:
            heappush(ready, name)
    seen = []
    ancestors = {}
    while ready:
        name = heappop(ready)
        row = index[name]
        ancestors[name] = row[1] is Effect.WRITE or any(
            ancestors[parent] for parent in row[3]
        )
        seen.append(name)
        for child in children[name]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heappush(ready, child)
    if len(seen) != len(names):
        raise DisconnectedRestartDependencyRejected("cyclic dependency")

    pinned_holds = []
    for name, item in zip(names, dependency.holds, strict=True):
        if type(item) is not _HOLD or item.step_id != name or type(item.reason) is not str:
            raise DisconnectedRestartDependencyRejected("quarantine hold identity mismatch")
        _, effect, state, parents = index[name]
        if effect is Effect.WRITE:
            expected_reason = "QUARANTINE_WRITE_ALL_STATES"
        elif ancestors[name]:
            expected_reason = "HOLD_TRANSITIVE_WRITE_ANCESTOR"
        elif state is StepState.RUNNING:
            expected_reason = "HOLD_RUNNING_READ_UNCERTAIN"
        elif state is not StepState.PENDING:
            expected_reason = "HOLD_TERMINAL_READ_UNVERIFIED"
        elif parents:
            expected_reason = "HOLD_DEPENDENCY_UNVERIFIED"
        else:
            expected_reason = "HOLD_UNAUTHORIZED_MOCK_REVIEW"
        if item.reason != expected_reason:
            raise DisconnectedRestartDependencyRejected("quarantine reason changed")
        pinned_holds.append((item, name, expected_reason))

    def stable() -> None:
        _require_original_contract()
        if (
            tuple(getattr(retained_tail, name) for name in tail_fields) != retained
            or tuple(getattr(recovered.tail, name) for name in tail_fields) != observed
            or recovered.step_statuses is not statuses
            or recovered.ambiguous_running_steps != expected_running
            or dependency.holds is not holds_epoch
            or dependency.topology_digest != observed[0]
            or dependency.digest is not digest_epoch
            or any(item is not original or
                   (item.step_id, item.effect, item.state, item.depends_on) != row
                   for item, (original, row) in zip(claims, pinned_claims, strict=True))
            or any(item is not original or item.step_id != name or item.reason != reason
                   for item, original, name, reason in (
                       (entry, *values) for entry, values in
                       zip(dependency.holds, pinned_holds, strict=True)
                   ))
        ):
            raise DisconnectedRestartDependencyRejected("restart input epoch changed")

    holds_epoch = dependency.holds
    digest_epoch = dependency.digest
    stable()
    outcome = tuple(RestartDependencyHold(
        name, state, reason, state == StepState.RUNNING.value,
    ) for (name, state, _), (_, _, reason) in zip(
        pinned_statuses, pinned_holds, strict=True,
    ))
    payload = json.dumps(
        [observed, dependency.digest, [
            (item.step_id, item.recovered_state, item.reason, item.outcome_unknown)
            for item in outcome
        ]],
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    review_sha = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable()
    result = _RESULT(observed[0], observed[2], dependency.digest, outcome,
                     expected_running, review_sha)
    if (
        type(result) is not _RESULT
        or any(getattr(result, name) is not False
               for name in _ORIGINAL_DENIALS[_RESULT])
    ):
        raise DisconnectedRestartDependencyRejected("restart review result gained authority")
    stable()
    return result
