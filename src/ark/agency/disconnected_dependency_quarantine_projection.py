"""Deny-only dependency closure for a disconnected Planner WRITE quarantine.

This computes the transitive descendants of independently enumerated WRITE steps
and joins the existing synthetic multi-store matrix. It NEVER promotes a READ
to executable status: even a locally terminal READ has unverified effects.
Supplied plan topology and store observations are not external provenance.
No ToolBackend, clock, permission token, or SQLite mutation is used.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from heapq import heappop, heappush

from .contracts import Effect, StepState
from .synthetic_write_quarantine_matrix_review import (
    SyntheticQuarantineMatrixRejected,
    SyntheticWriteStoreObservation,
    diagnose_disconnected_write_quarantine,
)

_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_MAX_STEPS = 128
_MAX_EDGES = 4096
_DOMAIN = b"ARK-disconnected-dependency-quarantine-v1\0"


class DisconnectedDependencyQuarantineRejected(ValueError):
    """Plan or synthetic WRITE evidence cannot be reconciled safely."""


@dataclass(frozen=True, slots=True)
class DisconnectedDependencyClaim:
    step_id: str
    effect: Effect
    state: StepState
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DisconnectedDependencyHold:
    step_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class DisconnectedDependencyProjection:
    topology_digest: str
    matrix_digest: str
    holds: tuple[DisconnectedDependencyHold, ...]
    digest: str

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
    def independent_custody_proven(self) -> bool:
        return False


_RESULT = DisconnectedDependencyProjection
_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_outcome_verified", "independent_custody_proven",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[name] for name in _DENIALS)
_ORIGINAL_RESULT_INIT = vars(_RESULT)["__init__"]


def _identifier(value: object) -> bool:
    if type(value) is not str or not value.strip() or len(value) > 256:
        return False
    try:
        return len(value.encode("utf-8", "strict")) <= 256 and "\x00" not in value
    except UnicodeError:
        return False


def _require_denials() -> None:
    if (
        DisconnectedDependencyProjection is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DisconnectedDependencyQuarantineRejected("quarantine authority changed")


def review_disconnected_dependency_quarantine(
    *,
    topology_digest: str,
    claims: tuple[DisconnectedDependencyClaim, ...],
    independently_expected_write_ids: tuple[str, ...],
    observations: tuple[SyntheticWriteStoreObservation, ...],
) -> DisconnectedDependencyProjection:
    """Project WRITE ancestor quarantine across a bounded complete synthetic DAG.

    Every finding is a HOLD; no output is a mock execution authorization.
    The expected WRITE list must be independently retained, not reconstructed
    from the very recovered store being inspected.
    """
    _require_denials()
    if (
        type(topology_digest) is not str or _PLAN.fullmatch(topology_digest) is None
        or type(claims) is not tuple or not 1 <= len(claims) <= _MAX_STEPS
        or type(independently_expected_write_ids) is not tuple
        or type(observations) is not tuple
    ):
        raise DisconnectedDependencyQuarantineRejected("invalid dependency inputs")
    pinned = []
    for node in claims:
        if type(node) is not DisconnectedDependencyClaim:
            raise DisconnectedDependencyQuarantineRejected("exact dependency claims required")
        item = (node.step_id, node.effect, node.state, node.depends_on)
        if (
            not _identifier(item[0]) or type(item[1]) is not Effect
            or type(item[2]) is not StepState or type(item[3]) is not tuple
            or len(item[3]) > _MAX_STEPS
            or any(not _identifier(parent) for parent in item[3])
            or item[3] != tuple(sorted(set(item[3])))
            or item[0] in item[3]
        ):
            raise DisconnectedDependencyQuarantineRejected("invalid dependency claim")
        pinned.append((node, item))
    names = tuple(item[0] for _, item in pinned)
    if names != tuple(sorted(set(names))):
        raise DisconnectedDependencyQuarantineRejected("dependency claims must be complete sorted")
    write_ids = tuple(
        item[0] for _, item in pinned if item[1] is Effect.WRITE
    )
    if (
        not write_ids or write_ids != independently_expected_write_ids
        or len(observations) != len(write_ids)
    ):
        raise DisconnectedDependencyQuarantineRejected("WRITE inventory mismatch")

    index = {name: item for _, item in pinned for name in (item[0],)}
    edges = sum(len(item[3]) for _, item in pinned)
    if edges > _MAX_EDGES or any(
        parent not in index for _, item in pinned for parent in item[3]
    ):
        raise DisconnectedDependencyQuarantineRejected("unknown dependency or edge budget")

    def stable() -> None:
        _require_denials()
        if any(
            node is not original or (
                node.step_id, node.effect, node.state, node.depends_on
            ) != item or any(
                now is not old for now, old in zip(
                    (node.step_id, node.effect, node.state, node.depends_on),
                    item, strict=True,
                )
            )
            for node, item in pinned for original in (node,)
        ):
            raise DisconnectedDependencyQuarantineRejected("dependency evidence changed")

    # Kahn ordering rejects cycles without recursing on attacker-controlled DAGs.
    counts = {name: len(item[3]) for name, item in index.items()}
    children: dict[str, list[str]] = {name: [] for name in names}
    for name, item in index.items():
        for parent in item[3]:
            children[parent].append(name)
    ready: list[str] = []
    for name in names:
        if counts[name] == 0:
            heappush(ready, name)
    order: list[str] = []
    while ready:
        name = heappop(ready)
        order.append(name)
        for child in children[name]:
            counts[child] -= 1
            if counts[child] == 0:
                heappush(ready, child)
    if len(order) != len(names):
        raise DisconnectedDependencyQuarantineRejected("dependency cycle")

    stable()
    try:
        matrix = diagnose_disconnected_write_quarantine(
            topology_digest=topology_digest,
            independently_expected_step_ids=write_ids,
            observations=observations,
        )
    except SyntheticQuarantineMatrixRejected as exc:
        raise DisconnectedDependencyQuarantineRejected("WRITE matrix rejected") from exc
    stable()
    if (
        matrix.observed_write_step_ids != write_ids
        or matrix.topology_digest != topology_digest
        or matrix.dispatch_authorized is not False
        or matrix.automatic_replay_authorized is not False
        or matrix.external_outcome_known is not False
    ):
        raise DisconnectedDependencyQuarantineRejected("WRITE evidence gained authority")

    write_ancestors: dict[str, bool] = {}
    for name in order:
        item = index[name]
        write_ancestors[name] = item[1] is Effect.WRITE or any(
            write_ancestors[parent] for parent in item[3]
        )
    holds = []
    for name in names:
        _, effect, state, parents = index[name]
        if effect is Effect.WRITE:
            reason = "QUARANTINE_WRITE_ALL_STATES"
        elif write_ancestors[name]:
            reason = "HOLD_TRANSITIVE_WRITE_ANCESTOR"
        elif state is StepState.RUNNING:
            reason = "HOLD_RUNNING_READ_UNCERTAIN"
        elif state is not StepState.PENDING:
            reason = "HOLD_TERMINAL_READ_UNVERIFIED"
        elif parents:
            reason = "HOLD_DEPENDENCY_UNVERIFIED"
        else:
            reason = "HOLD_UNAUTHORIZED_MOCK_REVIEW"
        holds.append(DisconnectedDependencyHold(name, reason))
    stable()
    payload = json.dumps(
        (topology_digest, matrix.local_digest, [
            (name, item[1].value, item[2].value, item[3]) for name, item in index.items()
        ], [(hold.step_id, hold.reason) for hold in holds]),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable()
    _require_denials()
    review = _RESULT(topology_digest, matrix.local_digest, tuple(holds), digest)
    if (
        type(review) is not _RESULT or len(review.holds) != len(names)
        or any(getattr(review, name) is not False for name in _DENIALS)
    ):
        raise DisconnectedDependencyQuarantineRejected("quarantine result changed")
    stable()
    return review
