"""Passive transition review of two separately supplied UNAPPROVED V3 snapshots.

A new syntactically plausible field is not verified materialized bytes, human
approval, consent, budget authorization or license clearance. The before and
after mappings are not signed or authenticated; this never runs a model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .offline_snapshot_shape_review import (
    OfflineShapeRejected,
    UnapprovedSnapshotShapeReview,
    review_unapproved_v3_snapshot_shapes,
)
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_DOMAIN = b"ARK-v3-passive-readiness-transition-v1\0"
_DENIED = (
    "external_compute_authorized", "preflight_authorized",
    "real_training_authorized", "candidate_generation_authorized",
    "protected_v2_authorized", "promotion_authorized",
    "artifact_identity_verified", "human_approval_verified",
)


class PassiveTransitionRejected(ValueError):
    """Unapproved snapshot transition cannot be safely inspected."""


@dataclass(frozen=True, slots=True)
class PassiveReadinessTransition:
    before_sha256: str
    after_sha256: str
    newly_plausible_paths: tuple[str, ...]
    became_unresolved_paths: tuple[str, ...]
    newly_malformed_paths: tuple[str, ...]
    syntax_repaired_paths: tuple[str, ...]
    transition_sha256: str

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def preflight_authorized(self) -> bool:
        return False

    @property
    def real_training_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_v2_authorized(self) -> bool:
        return False

    @property
    def promotion_authorized(self) -> bool:
        return False

    @property
    def artifact_identity_verified(self) -> bool:
        return False

    @property
    def human_approval_verified(self) -> bool:
        return False


def review_passive_readiness_transition(
    before: dict, after: dict,
) -> PassiveReadinessTransition:
    """Name path-level syntax transitions; never mint execution authority.

    A field leaving UNRESOLVED for a malformed value is *not* newly
    plausible. A field repaired from malformed to a placeholder remains
    unresolved. Identical digests do not prove provenance or signoff.
    """
    if type(before) is not dict or type(after) is not dict:
        raise PassiveTransitionRejected("exact unapproved snapshot dictionaries required")
    try:
        old_epoch = _pin_json_tree(before)
        new_epoch = _pin_json_tree(after)

        def stable() -> None:
            _assert_json_tree_epoch(before, old_epoch)
            _assert_json_tree_epoch(after, new_epoch)

        def inspect(mapping: dict) -> UnapprovedSnapshotShapeReview:
            stable()
            result = review_unapproved_v3_snapshot_shapes(mapping)
            stable()
            if (
                type(result) is not UnapprovedSnapshotShapeReview
                or type(result.snapshot_sha256) is not str
                or len(result.snapshot_sha256) != 64
                or type(result.unresolved_paths) is not tuple
                or type(result.invalid_shape_paths) is not tuple
                or type(result.checked_path_count) is not int
                or result.checked_path_count != 26
                or set(result.unresolved_paths) & set(result.invalid_shape_paths)
                or any(type(path) is not str for path in (
                    *result.unresolved_paths, *result.invalid_shape_paths,
                ))
                or result.external_compute_authorized is not False
                or result.preflight_authorized is not False
                or result.real_training_authorized is not False
                or result.candidate_generation_authorized is not False
                or result.v2_opening_authorized is not False
                or result.promotion_authorized is not False
            ):
                raise PassiveTransitionRejected("unapproved shape review gained authority")
            stable()
            return result

        initial_before = inspect(before)
        initial_after = inspect(after)
        before_unresolved = set(initial_before.unresolved_paths)
        after_unresolved = set(initial_after.unresolved_paths)
        before_invalid = set(initial_before.invalid_shape_paths)
        after_invalid = set(initial_after.invalid_shape_paths)
        newly_plausible = tuple(sorted(
            before_unresolved - after_unresolved - after_invalid
        ))
        became_unresolved = tuple(sorted(after_unresolved - before_unresolved))
        newly_malformed = tuple(sorted(after_invalid - before_invalid))
        repaired = tuple(sorted(
            before_invalid - after_invalid - after_unresolved
        ))
        fields = (
            initial_before.snapshot_sha256, initial_after.snapshot_sha256,
            newly_plausible, became_unresolved, newly_malformed, repaired,
        )
        digest = hashlib.sha256(
            _DOMAIN + json.dumps(
                fields, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
            ).encode("ascii")
        ).hexdigest()
        report = PassiveReadinessTransition(*fields, digest)
        original = tuple(getattr(report, name) for name in (
            "before_sha256", "after_sha256", "newly_plausible_paths",
            "became_unresolved_paths", "newly_malformed_paths",
            "syntax_repaired_paths", "transition_sha256",
        ))
        descriptors = tuple(getattr(PassiveReadinessTransition, n) for n in _DENIED)

        def stable_report() -> None:
            if (
                type(report) is not PassiveReadinessTransition
                or tuple(getattr(report, n) for n in (
                    "before_sha256", "after_sha256", "newly_plausible_paths",
                    "became_unresolved_paths", "newly_malformed_paths",
                    "syntax_repaired_paths", "transition_sha256",
                )) != original
                or any(
                    getattr(PassiveReadinessTransition, n) is not desc
                    for n, desc in zip(_DENIED, descriptors, strict=True)
                )
            ):
                raise PassiveTransitionRejected("passive transition report changed")
            stable()

        stable_report()
        for name in _DENIED:
            if getattr(report, name) is not False:
                raise PassiveTransitionRejected("passive transition gained authority")
            stable_report()
        # Re-run both source reviews after reflective denial callbacks.
        if inspect(before) != initial_before or inspect(after) != initial_after:
            raise PassiveTransitionRejected("snapshot transition drifted")
        stable_report()
        return report
    except (
        OfflineShapeRejected, KeyError, TypeError, ValueError,
        OverflowError, RecursionError, UnicodeError,
    ) as exc:
        if type(exc) is PassiveTransitionRejected:
            raise
        raise PassiveTransitionRejected(
            "unapproved transition review unavailable"
        ) from exc
