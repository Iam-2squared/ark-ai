"""Inert all-SUCCEEDED READ evidence bundle across a recovered Planner DAG.

A successful step cannot borrow a sibling or ancestor's separate local READ
receipt. Every SUCCEEDED step needs its OWN independently reviewed fixture
link. This is still only a deterministic cross-journal diagnostic: neither
the Planner journal nor the READ journal authenticates real execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import disconnected_planner_success_receipt_review as single
from . import disconnected_registered_receipt_review as registered
from . import planner_journal_review as journal
from .contracts import PlanStep
from .disconnected_registered_fixture_join import RegisteredFixtureLink

_DOMAIN = b"ARK-planner-succeeded-read-bundle-v1\0"


class PlannerReadSuccessBundleRejected(ValueError):
    """An independently reviewed READ is missing or changed for a success."""


@dataclass(frozen=True, slots=True)
class PlannerReadSuccessBundle:
    topology_digest: str
    status_digest: str
    step_ids: tuple[str, ...]
    correlation_sha256s: tuple[str, ...]
    bundle_sha256: str

    @property
    def external_execution_proven(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT = PlannerReadSuccessBundle
_FIELDS = (
    "topology_digest", "status_digest", "step_ids",
    "correlation_sha256s", "bundle_sha256",
)
_DENIALS = (
    "external_execution_proven", "write_authorized",
    "dispatch_authorized", "automatic_replay_authorized",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINALS = tuple(vars(_RESULT).get(key) for key in _FIELDS + _DENIALS + _HOOKS)
_ORIGINAL_SINGLE_REVIEW = single.review_synthetic_succeeded_read_correlation
# The apparent success evidence is entirely derived from local, caller-held
# receipts. Do not permit later replacement of its primitive custody checks,
# including a False-only no-op substitute, to bless those receipts.
_ORIGINAL_SINGLE_ORIGINALS = single._originals
_ORIGINAL_TAIL_STABLE = journal._retained_tail_epoch_stable
_ORIGINAL_LINK_FIELDS = registered._LINK_FIELDS
_ORIGINAL_REVIEW_FIELDS = registered._REVIEW_FIELDS
# A locally derived hash is not execution proof, but an injected digest
# function or domain must not silently counterfeit the deterministic review.
# Capture the primitive implementations before fixture-controlled callbacks.
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
        raise PlannerReadSuccessBundleRejected(
            "bundle digest implementation or domain changed"
        )
    if (
        single._originals is not _ORIGINAL_SINGLE_ORIGINALS
        or journal._retained_tail_epoch_stable is not _ORIGINAL_TAIL_STABLE
        or registered._LINK_FIELDS is not _ORIGINAL_LINK_FIELDS
        or registered._REVIEW_FIELDS is not _ORIGINAL_REVIEW_FIELDS
    ):
        raise PlannerReadSuccessBundleRejected(
            "bundle dependency callback or schema changed"
        )
    _ORIGINAL_SINGLE_ORIGINALS()
    if (
        PlannerReadSuccessBundle is not _RESULT
        or (
            single.review_synthetic_succeeded_read_correlation
            is not _ORIGINAL_SINGLE_REVIEW
        )
        or any(
            vars(_RESULT).get(key) is not original
            for key, original in zip(_FIELDS + _DENIALS + _HOOKS, _ORIGINALS, strict=True)
        )
    ):
        raise PlannerReadSuccessBundleRejected("bundle output carrier changed or callback changed")


def review_synthetic_succeeded_read_bundle(
    recovered: journal.SyntheticPlanRecovery,
    steps: tuple[PlanStep, ...],
    evidence: tuple[tuple[RegisteredFixtureLink, registered.RegisteredReceiptReview], ...],
) -> PlannerReadSuccessBundle:
    """Join ALL succeeded step receipts, without dispatch, permission or replay.

    An eligible input is a recovered synthetic DAG, where every succeeded
    step, including every succeeded ancestor, has separately retained
    registered READ evidence. PENDING/FAILED/BLOCKED/UNKNOWN steps do not
    gain evidence or authority. Mixed registry revisions are rejected.
    """
    _originals()
    if (
        type(recovered) is not journal.SyntheticPlanRecovery
        or type(recovered.tail) is not journal.SyntheticPlanTail
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or any(type(step) is not PlanStep for step in steps)
        or type(evidence) is not tuple or not 1 <= len(evidence) <= len(steps)
        or any(
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not RegisteredFixtureLink
            or type(pair[1]) is not registered.RegisteredReceiptReview
            for pair in evidence
        )
        or type(recovered.step_statuses) is not tuple
        or type(recovered.ambiguous_running_steps) is not tuple
    ):
        raise PlannerReadSuccessBundleRejected("exact synthetic READ bundle inputs required")

    tail = recovered.tail
    statuses = recovered.step_statuses
    running = recovered.ambiguous_running_steps
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
    pair_epoch = tuple(
        (
            pair, pair[0], pair[1],
            tuple(getattr(pair[0], key) for key in registered._LINK_FIELDS),
            tuple(getattr(pair[1], key) for key in registered._REVIEW_FIELDS),
        )
        for pair in evidence
    )

    def stable() -> None:
        _originals()
        if (
            recovered.tail is not tail
            or recovered.step_statuses is not statuses
            or recovered.ambiguous_running_steps is not running
            or not journal._retained_tail_epoch_stable(tail, tail_epoch)
            or any(
                step is not old or step.step_id is not name
                or step.call is not call or step.depends_on is not deps
                or call.tool is not tool or call.capability is not capability
                or call.scope is not scope or call.arguments is not arguments
                or call.request_id != request_id
                for step, (
                    old, name, call, deps, tool, capability, scope,
                    arguments, request_id,
                ) in zip(steps, step_epoch, strict=True)
            )
            or any(
                pair is not old_pair or pair[0] is not link or pair[1] is not review
                or any(
                    getattr(link, key) is not old
                    for key, old in zip(registered._LINK_FIELDS, link_fields, strict=True)
                )
                or any(
                    getattr(review, key) is not old
                    for key, old in zip(registered._REVIEW_FIELDS, review_fields, strict=True)
                )
                for pair, (
                    old_pair, link, review, link_fields, review_fields,
                ) in zip(evidence, pair_epoch, strict=True)
            )
        ):
            raise PlannerReadSuccessBundleRejected("bundle evidence changed during review")

    stable()
    if (
        len(statuses) != len(steps)
        or any(
            type(row) is not tuple or len(row) != 3
            or type(row[0]) is not str or type(row[1]) is not str
            or type(row[2]) is not int or not 0 <= row[2] <= (1 << 63) - 1
            for row in statuses
        )
    ):
        raise PlannerReadSuccessBundleRejected("malformed Planner status membership")
    states = {name: state for name, state, _revision in statuses}
    succeeded = {name for name, state in states.items() if state == "succeeded"}
    identifiers = [fields[0] for _pair, _link, _review, fields, _rf in pair_epoch]
    if (
        len(states) != len(statuses)
        or set(states) != {step.step_id for step in steps}
        or not succeeded or len(succeeded) != len(evidence)
        or set(identifiers) != succeeded
        or len(set(identifiers)) != len(identifiers)
        or len({fields[2] for _pair, _link, _review, fields, _rf in pair_epoch})
        != len(pair_epoch)
        or len({fields[7] for _pair, _link, _review, fields, _rf in pair_epoch})
        != len(pair_epoch)
        or len({fields[3] for _pair, _link, _review, fields, _rf in pair_epoch}) != 1
        or any(
            any(dep not in succeeded for dep in step.depends_on)
            for step in steps if step.step_id in succeeded
        )
    ):
        raise PlannerReadSuccessBundleRejected(
            "every succeeded step requires unique same-registry READ evidence"
        )

    correlated = []
    for _pair, link, review, _lf, _rf in pair_epoch:
        stable()
        try:
            receipt = single.review_synthetic_succeeded_read_correlation(
                recovered, steps, link, review,
            )
        except (single.PlannerSucceededReadCorrelationRejected, ValueError) as exc:
            raise PlannerReadSuccessBundleRejected(
                "one synthetic succeeded READ has no exact reviewed receipt"
            ) from exc
        stable()
        if (
            type(receipt) is not single.PlannerSucceededReadCorrelation
            or receipt.step_id not in succeeded
            or any(getattr(receipt, name) is not False for name in single._DENIALS)
        ):
            raise PlannerReadSuccessBundleRejected("succeeded READ gained authority")
        stable()
        correlated.append((receipt.step_id, receipt.correlation_sha256))

    correlated.sort()
    ids = tuple(name for name, _digest in correlated)
    digests = tuple(digest for _name, digest in correlated)
    fields = (tail_epoch[0], tail_epoch[3], ids, digests)
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()
    stable()
    report = _RESULT(*fields, digest)
    stable()
    if (
        type(report) is not _RESULT
        or any(
            getattr(report, key) is not value
            for key, value in zip(_FIELDS, (*fields, digest), strict=True)
        )
    ):
        raise PlannerReadSuccessBundleRejected("bundle output changed")
    for name in _DENIALS:
        _originals()
        if getattr(report, name) is not False:
            raise PlannerReadSuccessBundleRejected("bundle granted execution authority")
        stable()
    if any(
        getattr(report, key) is not value
        for key, value in zip(_FIELDS, (*fields, digest), strict=True)
    ):
        raise PlannerReadSuccessBundleRejected("bundle result changed after denial")
    stable()
    return report
