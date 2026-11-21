"""Detached self-consistency check for a synthetic Planner dependency receipt.

This compares canonical local bytes with a claimed digest. It does not
reconstruct the WRITE store observations, prove independently complete inputs,
unquarantine an action, dispatch a backend or authenticate any event.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import disconnected_dependency_quarantine_projection as projection_module
from .contracts import Effect, StepState

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MATRIX = re.compile(r"quarantine_[0-9a-f]{64}\Z")
_REPORT_DOMAIN = b"ARK-detached-dependency-receipt-review-v1\0"
_MAX_STEPS = 128
_MAX_EDGES = 4096

_ORIGINAL_GUARD = projection_module._require_denials
_ORIGINAL_CLASSES = (
    projection_module.DisconnectedDependencyClaim,
    projection_module.DisconnectedDependencyHold,
    projection_module.DisconnectedDependencyProjection,
)
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_PROTOCOL = (_SHA, _MATRIX, _REPORT_DOMAIN, _MAX_STEPS, _MAX_EDGES)
_ORIGINAL_SOURCE_DOMAIN = projection_module._DOMAIN


class DetachedDependencyDigestRejected(ValueError):
    """A local dependency receipt is not self-consistent."""


@dataclass(frozen=True, slots=True)
class DetachedDependencyDigestReview:
    topology_digest: str
    quarantine_digest: str
    review_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_provenance_verified(self) -> bool:
        return False


_RESULT = DetachedDependencyDigestReview
_RESULT_NAMES = (
    "topology_digest", "quarantine_digest", "review_sha256",
    "dispatch_authorized", "automatic_replay_authorized",
    "external_provenance_verified", "__init__", "__new__",
    "__getattribute__", "__getattr__",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _RESULT_NAMES)


def _protocol() -> None:
    if (
        projection_module._require_denials is not _ORIGINAL_GUARD
        or projection_module._DOMAIN is not _ORIGINAL_SOURCE_DOMAIN
        or (
            projection_module.DisconnectedDependencyClaim,
            projection_module.DisconnectedDependencyHold,
            projection_module.DisconnectedDependencyProjection,
        ) != _ORIGINAL_CLASSES
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or _SHA is not _ORIGINAL_PROTOCOL[0]
        or _MATRIX is not _ORIGINAL_PROTOCOL[1]
        or _REPORT_DOMAIN is not _ORIGINAL_PROTOCOL[2]
        or type(_MAX_STEPS) is not int
        or type(_MAX_EDGES) is not int
        or (_MAX_STEPS, _MAX_EDGES) != _ORIGINAL_PROTOCOL[3:]
        or DetachedDependencyDigestReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_RESULT_NAMES, _ORIGINAL_RESULT, strict=True)
        )
    ):
        raise DetachedDependencyDigestRejected("dependency digest protocol changed")
    try:
        _ORIGINAL_GUARD()
    except projection_module.DisconnectedDependencyQuarantineRejected as exc:
        raise DetachedDependencyDigestRejected("source dependency protocol changed") from exc


def _identifier(value: object) -> bool:
    if type(value) is not str or not value.strip() or len(value) > 256:
        return False
    try:
        return "\x00" not in value and len(value.encode("utf-8", "strict")) <= 256
    except UnicodeError:
        return False


def review_detached_dependency_digest(
    *,
    claims: tuple[projection_module.DisconnectedDependencyClaim, ...],
    projection: projection_module.DisconnectedDependencyProjection,
) -> DetachedDependencyDigestReview:
    """Verify a bounded local transcript digest, never execution permission."""
    _protocol()
    if (
        type(claims) is not tuple or not 1 <= len(claims) <= _MAX_STEPS
        or type(projection) is not _ORIGINAL_CLASSES[2]
        or type(projection.topology_digest) is not str
        or projection_module._PLAN.fullmatch(projection.topology_digest) is None
        or type(projection.matrix_digest) is not str
        or _MATRIX.fullmatch(projection.matrix_digest) is None
        or type(projection.digest) is not str
        or _SHA.fullmatch(projection.digest) is None
        or type(projection.holds) is not tuple
        or len(projection.holds) != len(claims)
    ):
        raise DetachedDependencyDigestRejected("dependency digest input shape invalid")

    rows = []
    holds = []
    for claim, hold in zip(claims, projection.holds, strict=True):
        _protocol()
        if type(claim) is not _ORIGINAL_CLASSES[0] or type(hold) is not _ORIGINAL_CLASSES[1]:
            raise DetachedDependencyDigestRejected("inexact dependency carrier")
        fields = (claim.step_id, claim.effect, claim.state, claim.depends_on)
        if (
            not _identifier(fields[0])
            or type(fields[1]) is not Effect or type(fields[2]) is not StepState
            or type(fields[3]) is not tuple or len(fields[3]) > _MAX_STEPS
            or fields[3] != tuple(sorted(set(fields[3])))
            or any(not _identifier(parent) for parent in fields[3])
            or fields[0] in fields[3]
            or hold.step_id != fields[0] or type(hold.reason) is not str
            or not 1 <= len(hold.reason) <= 64 or not hold.reason.isascii()
        ):
            raise DetachedDependencyDigestRejected("invalid dependency digest transcript")
        rows.append((claim, fields))
        holds.append((hold, (hold.step_id, hold.reason)))

    names = tuple(fields[0] for _, fields in rows)
    if (
        names != tuple(sorted(set(names)))
        or sum(len(fields[3]) for _, fields in rows) > _MAX_EDGES
        or any(parent not in names for _, fields in rows for parent in fields[3])
    ):
        raise DetachedDependencyDigestRejected("incomplete dependency digest topology")

    epoch = (
        projection.topology_digest, projection.matrix_digest,
        projection.holds, projection.digest,
    )

    def stable() -> None:
        _protocol()
        if (
            any(
                (claim.step_id, claim.effect, claim.state, claim.depends_on) != fields
                for claim, fields in rows
            )
            or any((hold.step_id, hold.reason) != fields for hold, fields in holds)
            or any(
                actual is not original for actual, original in zip(
                    (
                        projection.topology_digest, projection.matrix_digest,
                        projection.holds, projection.digest,
                    ), epoch, strict=True,
                )
            )
        ):
            raise DetachedDependencyDigestRejected("dependency receipt epoch changed")

    stable()
    payload = json.dumps(
        (
            epoch[0], epoch[1],
            [(fields[0], fields[1].value, fields[2].value, fields[3])
             for _, fields in rows],
            [values for _, values in holds],
        ), ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    expected = hashlib.sha256(_ORIGINAL_SOURCE_DOMAIN + payload).hexdigest()
    stable()
    if expected != projection.digest:
        raise DetachedDependencyDigestRejected("dependency receipt digest mismatch")
    for denial in (
        "dispatch_authorized", "automatic_replay_authorized",
        "external_outcome_verified", "independent_custody_proven",
    ):
        _protocol()
        if getattr(projection, denial) is not False:
            raise DetachedDependencyDigestRejected("dependency source gained authority")
        stable()
    raw = json.dumps(
        (epoch[0], epoch[1], expected, len(rows)),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    review_hash = hashlib.sha256(_REPORT_DOMAIN + raw).hexdigest()
    stable()
    report = _RESULT(epoch[0], expected, review_hash)
    _protocol()
    if (
        type(report) is not _RESULT
        or report.topology_digest != epoch[0]
        or report.quarantine_digest != expected
        or report.review_sha256 != review_hash
        or any(
            getattr(report, name) is not False for name in (
                "dispatch_authorized", "automatic_replay_authorized",
                "external_provenance_verified",
            )
        )
    ):
        raise DetachedDependencyDigestRejected("detached receipt gained authority")
    stable()
    return report
