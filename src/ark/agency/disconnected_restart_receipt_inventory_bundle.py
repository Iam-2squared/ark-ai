"""Offline cross-check of a recovered Planner, WRITE inventory and DAG receipt.

The three local verifiers cover different evidence.  A self-consistent DAG
digest alone is insufficient: bind it to the *independently supplied* complete
WRITE inventory and separately recovered journal tail.  No input has
authenticated custody, no cross-store atomicity is claimed, and every step
remains HOLD.  This module contains no executor, retry or store mutator.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import disconnected_dependency_digest_review as digest_module
from . import disconnected_dependency_quarantine_projection as dependency_module
from . import disconnected_restart_dependency_join as restart_module
from .disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyProjection,
)
from .planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail
from .synthetic_write_quarantine_matrix_review import SyntheticWriteStoreObservation

_DOMAIN = b"ARK-disconnected-restart-receipt-inventory-bundle-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_STEPS = 128

_ORIGINAL_CALLEES = (
    dependency_module.review_disconnected_dependency_quarantine,
    digest_module.review_detached_dependency_digest,
    restart_module.review_disconnected_restart_dependency,
)
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_PROTOCOL = (_DOMAIN, _SHA, _MAX_STEPS)


class DisconnectedRestartReceiptBundleRejected(ValueError):
    """Independent-looking local witnesses are inconsistent or incomplete."""


@dataclass(frozen=True, slots=True)
class DisconnectedRestartReceiptBundle:
    topology_digest: str
    event_hash: str
    matrix_digest: str
    quarantine_digest: str
    detached_review_sha256: str
    restart_review_sha256: str
    held_step_ids: tuple[str, ...]
    unknown_step_ids: tuple[str, ...]
    bundle_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def independent_inventory_verified(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False


_RESULT = DisconnectedRestartReceiptBundle
_RESULT_NAMES = (
    "topology_digest", "event_hash", "matrix_digest", "quarantine_digest",
    "detached_review_sha256", "restart_review_sha256", "held_step_ids",
    "unknown_step_ids", "bundle_sha256", "__init__", "__new__",
    "__getattribute__", "__getattr__", "dispatch_authorized",
    "automatic_replay_authorized", "independent_inventory_verified",
    "external_outcome_verified",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _RESULT_NAMES)


def _protocol() -> None:
    if (
        (_DOMAIN, _SHA, _MAX_STEPS) != _ORIGINAL_PROTOCOL
        or type(_MAX_STEPS) is not int
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or (
            dependency_module.review_disconnected_dependency_quarantine,
            digest_module.review_detached_dependency_digest,
            restart_module.review_disconnected_restart_dependency,
        ) != _ORIGINAL_CALLEES
        or DisconnectedRestartReceiptBundle is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_RESULT_NAMES, _ORIGINAL_RESULT, strict=True)
        )
    ):
        raise DisconnectedRestartReceiptBundleRejected("bundle protocol changed")


def _projection_image(
    item: DisconnectedDependencyProjection,
) -> tuple[str, str, tuple[tuple[str, str], ...], str]:
    if type(item) is not DisconnectedDependencyProjection or type(item.holds) is not tuple:
        raise DisconnectedRestartReceiptBundleRejected("inexact dependency receipt")
    return (
        item.topology_digest, item.matrix_digest,
        tuple((hold.step_id, hold.reason) for hold in item.holds),
        item.digest,
    )


def review_disconnected_restart_receipt_bundle(
    *,
    recovered: SyntheticPlanRecovery,
    retained_tail: SyntheticPlanTail,
    claims: tuple[DisconnectedDependencyClaim, ...],
    independently_expected_write_ids: tuple[str, ...],
    observations: tuple[SyntheticWriteStoreObservation, ...],
    dependency: DisconnectedDependencyProjection,
) -> DisconnectedRestartReceiptBundle:
    """Recompute the local WRITE matrix, verify DAG bytes and bind journal HOLD.

    The independent WRITE inventory is a caller-supplied claim; if the caller
    omitted a WRITE from *all* sources no local digest can discover it.  A
    matching bundle is diagnostic evidence, NEVER authorization to dispatch.
    """
    _protocol()
    if (
        type(recovered) is not SyntheticPlanRecovery
        or type(retained_tail) is not SyntheticPlanTail
        or type(dependency) is not DisconnectedDependencyProjection
        or type(claims) is not tuple or not 1 <= len(claims) <= _MAX_STEPS
        or type(independently_expected_write_ids) is not tuple
        or type(observations) is not tuple
    ):
        raise DisconnectedRestartReceiptBundleRejected("bundle input shape invalid")

    try:
        # The independent inventory is checked by the original matrix reviewer;
        # the detached digest additionally replays the exact source DAG bytes.
        initial = _projection_image(dependency)
        canonical = dependency_module.review_disconnected_dependency_quarantine(
            topology_digest=retained_tail.topology_digest,
            claims=claims,
            independently_expected_write_ids=independently_expected_write_ids,
            observations=observations,
        )
        if initial != _projection_image(canonical):
            raise DisconnectedRestartReceiptBundleRejected(
                "WRITE inventory and retained dependency receipt disagree"
            )
        detached = digest_module.review_detached_dependency_digest(
            claims=claims, projection=dependency,
        )
        restart = restart_module.review_disconnected_restart_dependency(
            recovered=recovered, dependency=dependency,
            claims=claims, retained_tail=retained_tail,
        )
        if (
            detached.topology_digest != restart.topology_digest
            or detached.quarantine_digest != restart.quarantine_digest
            or restart.plan_event_hash != recovered.tail.event_hash
            or restart.plan_event_hash != retained_tail.event_hash
            or detached.quarantine_digest != canonical.digest
            or any(
                getattr(result, flag) is not False
                for result, flags in (
                    (detached, (
                        "dispatch_authorized", "automatic_replay_authorized",
                        "external_provenance_verified",
                    )),
                    (restart, (
                        "dispatch_authorized", "automatic_replay_authorized",
                        "external_outcome_verified", "trusted_provenance_verified",
                    )),
                )
                for flag in flags
            )
        ):
            raise DisconnectedRestartReceiptBundleRejected("review receipts disagree")

        held = tuple(item.step_id for item in restart.holds)
        unknown = restart.uncertain_step_ids
        payload = json.dumps(
            (
                restart.topology_digest, restart.plan_event_hash,
                canonical.matrix_digest, canonical.digest,
                detached.review_sha256, restart.review_sha256, held, unknown,
            ),
            ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        ).encode("ascii")
        bundle_hash = hashlib.sha256(_DOMAIN + payload).hexdigest()

        # Second full inventory replay detects drift between the two separated
        # verifier calls.  A matching result still cannot prove store atomicity.
        _protocol()
        final = dependency_module.review_disconnected_dependency_quarantine(
            topology_digest=retained_tail.topology_digest,
            claims=claims,
            independently_expected_write_ids=independently_expected_write_ids,
            observations=observations,
        )
        if _projection_image(final) != initial or _projection_image(dependency) != initial:
            raise DisconnectedRestartReceiptBundleRejected("bundle inputs changed")
        if type(bundle_hash) is not str or _SHA.fullmatch(bundle_hash) is None:
            raise DisconnectedRestartReceiptBundleRejected("bundle digest malformed")
    except (
        dependency_module.DisconnectedDependencyQuarantineRejected,
        digest_module.DetachedDependencyDigestRejected,
        restart_module.DisconnectedRestartDependencyRejected,
    ) as exc:
        raise DisconnectedRestartReceiptBundleRejected(
            "bundle source verification rejected"
        ) from exc

    result = _RESULT(
        restart.topology_digest, restart.plan_event_hash,
        canonical.matrix_digest, canonical.digest,
        detached.review_sha256, restart.review_sha256, held, unknown, bundle_hash,
    )
    _protocol()
    if (
        type(result) is not _RESULT
        or result.bundle_sha256 != bundle_hash
        or any(
            getattr(result, flag) is not False
            for flag in (
                "dispatch_authorized", "automatic_replay_authorized",
                "independent_inventory_verified", "external_outcome_verified",
            )
        )
    ):
        raise DisconnectedRestartReceiptBundleRejected("bundle gained authority")
    return result
