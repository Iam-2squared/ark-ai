"""Inert, cross-journal Planner SUCCEEDED/registered fixture READ correlation.

The caller must first recover the Planner SQLite journal against independently
retained plan history and separately review the registered READ SQLite journal.
This *post-review join* does no I/O and cannot authenticate either caller-held
receipt, provide an atomic transaction spanning journals, or prove an external
tool ran. It deliberately does NOT enable SUCCEEDED in the normal Planner
recovery projection or authorize dispatch/replay.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import disconnected_registered_receipt_review as registered
from . import planner_journal_review as journal
from .contracts import PlanConflictError, PlanStep
from .disconnected_registered_fixture_join import RegisteredFixtureLink
from .planner import PlanGraph, _plan_digest

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-planner-succeeded-registered-read-correlation-v1\0"


class PlannerSucceededReadCorrelationRejected(ValueError):
    """A synthetic success or independent READ witness is not correlated."""


@dataclass(frozen=True, slots=True)
class PlannerSucceededReadCorrelation:
    topology_digest: str
    status_digest: str
    step_id: str
    action_request_id: str
    registry_revision: str
    result_sha256: str
    journal_tip_sha256: str
    correlation_sha256: str

    @property
    def independent_execution_proven(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT = PlannerSucceededReadCorrelation
_FIELDS = (
    "topology_digest", "status_digest", "step_id", "action_request_id",
    "registry_revision", "result_sha256", "journal_tip_sha256",
    "correlation_sha256",
)
_DENIALS = (
    "independent_execution_proven", "external_outcome_verified",
    "dispatch_authorized", "automatic_replay_authorized",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL = tuple(vars(_RESULT).get(name) for name in _FIELDS + _DENIALS + _HOOKS)
# The per-step join is also callable without the outer all-success bundle.
# Pin its local digest primitives and domain before inspecting any supplied
# recovered/journal evidence; digest equality is never independent custody.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


def _originals() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise PlannerSucceededReadCorrelationRejected(
            "correlation digest implementation or domain changed"
        )
    journal._require_original_recovery_denials()
    registered._assert_original_denial_definitions()
    if (
        PlannerSucceededReadCorrelation is not _RESULT
        or any(
            vars(_RESULT).get(name) is not old
            for name, old in zip(_FIELDS + _DENIALS + _HOOKS, _ORIGINAL, strict=True)
        )
    ):
        raise PlannerSucceededReadCorrelationRejected(
            "synthetic Planner correlation carrier changed"
        )


def review_synthetic_succeeded_read_correlation(
    recovered: journal.SyntheticPlanRecovery,
    steps: tuple[PlanStep, ...],
    link: RegisteredFixtureLink,
    read_review: registered.RegisteredReceiptReview,
) -> PlannerSucceededReadCorrelation:
    """Correlate exact detached READ evidence with one persisted SUCCEEDED step.

    The separately checked registered receipt remains only evidence of a
    *fixture* READ. A success label is not permission or real-world evidence.
    Missing/replaced evidence, WRITE, UNKNOWN and inconsistent recovery fail
    closed. This module never executes a ToolBackend or opens either journal.
    """
    _originals()
    if (
        type(recovered) is not journal.SyntheticPlanRecovery
        or type(recovered.tail) is not journal.SyntheticPlanTail
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or any(type(step) is not PlanStep for step in steps)
        or type(link) is not RegisteredFixtureLink
        or type(read_review) is not registered.RegisteredReceiptReview
    ):
        raise PlannerSucceededReadCorrelationRejected("exact reviewed READ inputs required")

    tail, statuses, ambiguous = (
        recovered.tail, recovered.step_statuses, recovered.ambiguous_running_steps,
    )
    tail_epoch = (
        tail.topology_digest, tail.event_count, tail.event_hash,
        tail.status_digest, tail.last_at_ms,
    )
    step_epoch = tuple(
        (
            step, step.step_id, step.call, step.depends_on,
            step.call.tool, step.call.capability, step.call.scope,
            step.call.arguments, step.call.request_id,
        )
        for step in steps
    )
    link_epoch = tuple(getattr(link, name) for name in registered._LINK_FIELDS)
    review_epoch = tuple(getattr(read_review, name) for name in registered._REVIEW_FIELDS)

    def stable() -> None:
        _originals()
        if (
            recovered.tail is not tail
            or recovered.step_statuses is not statuses
            or recovered.ambiguous_running_steps is not ambiguous
            or not journal._retained_tail_epoch_stable(tail, tail_epoch)
            or any(
                a is not b for a, b in zip(
                    (getattr(link, key) for key in registered._LINK_FIELDS),
                    link_epoch, strict=True,
                )
            )
            or any(
                a is not b for a, b in zip(
                    (getattr(read_review, key) for key in registered._REVIEW_FIELDS),
                    review_epoch, strict=True,
                )
            )
            or any(
                step is not original or step.step_id is not name
                or step.call is not call or step.depends_on is not deps
                or call.tool is not tool or call.capability is not capability
                or call.scope is not scope or call.arguments is not args
                or call.request_id != request_id
                for step, (
                    original, name, call, deps, tool, capability, scope, args,
                    request_id,
                ) in zip(steps, step_epoch, strict=True)
            )
        ):
            raise PlannerSucceededReadCorrelationRejected(
                "Planner or registered READ input changed during correlation"
            )

    stable()
    try:
        tail.assert_shape()
        graph = PlanGraph(steps)
        topology = graph.topology_digest()
    except (PlanConflictError, TypeError, ValueError) as exc:
        raise PlannerSucceededReadCorrelationRejected(
            "Planner exact topology unavailable"
        ) from exc
    stable()
    if topology != tail_epoch[0]:
        raise PlannerSucceededReadCorrelationRejected(
            "registered READ belongs to another Planner topology"
        )
    if (
        type(statuses) is not tuple or len(statuses) != len(steps)
        or type(ambiguous) is not tuple
        or any(
            type(row) is not tuple or len(row) != 3
            or type(row[0]) is not str or type(row[1]) is not str
            or type(row[2]) is not int or not 0 <= row[2] <= (1 << 63) - 1
            for row in statuses
        )
    ):
        raise PlannerSucceededReadCorrelationRejected("malformed Planner status image")
    state_map = {name: (state, revision) for name, state, revision in statuses}
    if (
        len(state_map) != len(statuses)
        or set(state_map) != {s.step_id for s in steps}
        or ambiguous != tuple(
            sorted(name for name, (state, _) in state_map.items() if state == "running")
        )
    ):
        raise PlannerSucceededReadCorrelationRejected("Planner status membership drift")
    digest = _plan_digest(
        "pstate_",
        {
            "schema_version": 1,
            "topology_digest": topology,
            "statuses": [
                {"step_id": name, "state": state_map[name][0],
                 "revision": state_map[name][1]}
                for name in sorted(state_map)
            ],
        },
    )
    stable()
    if digest != tail_epoch[3]:
        raise PlannerSucceededReadCorrelationRejected("Planner status digest drift")

    step_map = {step.step_id: step for step in steps}
    target = step_map.get(link_epoch[0])
    if (
        target is None
        or state_map[target.step_id][0] != "succeeded"
        or state_map[target.step_id][1] < 2
        or any(state_map[dep][0] != "succeeded" for dep in target.depends_on)
        or target.call.request_id != link_epoch[1]
        or type(link_epoch[3]) is not str
        or type(link_epoch[6]) is not str or _SHA.fullmatch(link_epoch[6]) is None
        or type(review_epoch[4]) is not int or review_epoch[4] < 1
        or type(review_epoch[5]) is not str
        or _SHA.fullmatch(review_epoch[5]) is None
        or (
            review_epoch[0], review_epoch[1], review_epoch[2], review_epoch[3]
        ) != (link_epoch[0], link_epoch[1], link_epoch[2], link_epoch[7])
        or any(getattr(link, name) is not False for name in registered._LINK_DENIALS)
        or any(getattr(read_review, name) is not False
               for name in registered._REVIEW_DENIALS)
    ):
        raise PlannerSucceededReadCorrelationRejected(
            "SUCCEEDED READ lacks exact independently reviewed fixture correlation"
        )
    stable()
    fields = (
        topology, digest, link_epoch[0], link_epoch[1], link_epoch[3],
        link_epoch[6], review_epoch[5],
    )
    correlation = hashlib.sha256(
        _DOMAIN + json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()
    stable()
    _originals()
    report = _RESULT(*fields, correlation)
    stable()
    if (
        type(report) is not _RESULT
        or any(getattr(report, name) is not value
               for name, value in zip(_FIELDS, (*fields, correlation), strict=True))
    ):
        raise PlannerSucceededReadCorrelationRejected("correlation receipt changed")
    for name in _DENIALS:
        _originals()
        if getattr(report, name) is not False:
            raise PlannerSucceededReadCorrelationRejected("correlation gained authority")
        stable()
    return report
