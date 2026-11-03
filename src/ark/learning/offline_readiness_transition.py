"""Passive transition review of two separately supplied UNAPPROVED V3 snapshots.

A new syntactically plausible field is not verified materialized bytes, human
approval, consent, budget authorization or license clearance. The before and
after mappings are not signed or authenticated; this never runs a model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .offline_readiness_inventory import _PLACEHOLDERS, _SECTIONS
from .offline_snapshot_shape_review import (
    OfflineShapeRejected,
    UnapprovedSnapshotShapeReview,
    _plausible_shape,
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


# Keep the original passive authority surface across independently supplied
# snapshots. A false-only callback patched before a review starts is still a
# substituted implementation and must not become the late-call baseline.
_TRANSITION_TYPE = PassiveReadinessTransition
_ORIGINAL_TRANSITION_DENIALS = tuple(vars(_TRANSITION_TYPE)[key] for key in _DENIED)
# The child shape report is another authority-bearing callback surface.
# Pin it at import, not after the two unapproved snapshots have been parsed.
_SOURCE_TYPE = UnapprovedSnapshotShapeReview
_SOURCE_DENIALS = (
    "external_compute_authorized", "preflight_authorized",
    "real_training_authorized", "candidate_generation_authorized",
    "v2_opening_authorized", "promotion_authorized",
)
_ORIGINAL_SOURCE_DENIALS = tuple(vars(_SOURCE_TYPE)[key] for key in _SOURCE_DENIALS)


def _assert_original_passive_authority() -> None:
    if (
        PassiveReadinessTransition is not _TRANSITION_TYPE
        or UnapprovedSnapshotShapeReview is not _SOURCE_TYPE
        or any(
            vars(_TRANSITION_TYPE).get(key) is not original
            for key, original in zip(
                _DENIED, _ORIGINAL_TRANSITION_DENIALS, strict=True,
            )
        )
        or any(
            vars(_SOURCE_TYPE).get(key) is not original
            for key, original in zip(
                _SOURCE_DENIALS, _ORIGINAL_SOURCE_DENIALS, strict=True,
            )
        )
    ):
        raise PassiveTransitionRejected("original passive authority changed")


def _independent_shape_paths(mapping: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Derive visible syntax categories from input, never from the shape callback.

    This is a review guard only: syntax cannot establish actual artifact
    identity, human authorization or billable compute permission.
    """
    unresolved: set[str] = set()
    invalid: set[str] = set()
    for section, names in _SECTIONS.items():
        values = mapping[section]
        if type(values) is not dict:
            raise PassiveTransitionRejected("unapproved shape section invalid")
        for name in names:
            path = f"{section}.{name}"
            value = values[name]
            if type(value) is str and value in _PLACEHOLDERS:
                unresolved.add(path)
            elif not _plausible_shape(path, value):
                invalid.add(path)
    alias = mapping["tokenizer"]["revision"]
    base = mapping["base"]["revision"]
    if alias == "SAME_AS_BASE":
        if type(base) is str and base in _PLACEHOLDERS:
            unresolved.add("tokenizer.revision")
        elif not _plausible_shape("base.revision", base):
            invalid.add("tokenizer.revision")
    elif type(alias) is str and alias in _PLACEHOLDERS:
        unresolved.add("tokenizer.revision")
    elif not _plausible_shape("base.revision", alias):
        invalid.add("tokenizer.revision")
    return tuple(sorted(unresolved)), tuple(sorted(invalid))


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
    _assert_original_passive_authority()
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
            # An exact-type shape callback is not itself an immutable file
            # identity. Independently bind its reported SHA to the canonical
            # bytes of the still-unapproved source snapshot.
            canonical = json.dumps(
                mapping, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ).encode("utf-8")
            if result.snapshot_sha256 != hashlib.sha256(canonical).hexdigest():
                raise PassiveTransitionRejected("shape callback digest mismatch")
            # An exact-class callback with the correct SHA can still invent
            # path categories and fabricate apparent readiness progress.
            expected_unresolved, expected_invalid = _independent_shape_paths(mapping)
            if (
                result.unresolved_paths != expected_unresolved
                or result.invalid_shape_paths != expected_invalid
            ):
                raise PassiveTransitionRejected("shape callback path classification mismatch")
            stable()
            return result

        initial_before = inspect(before)
        initial_after = inspect(after)
        report_fields = (
            "snapshot_sha256", "unresolved_paths",
            "invalid_shape_paths", "checked_path_count",
        )
        source_reports = (initial_before, initial_after)
        source_epochs = tuple(
            tuple(getattr(result, name) for name in report_fields)
            for result in source_reports
        )
        # A denied-only transition getter can still rebind a source report's
        # False-valued authority descriptor. Retain exact original class
        # descriptors through the *last* independent reinspection; neither
        # source report is an approval or an authenticated material identity.
        source_denials = _SOURCE_DENIALS
        source_descriptors = _ORIGINAL_SOURCE_DENIALS

        def stable_source_reports() -> None:
            if any(
                getattr(UnapprovedSnapshotShapeReview, name) is not original
                for name, original in zip(
                    source_denials, source_descriptors, strict=True,
                )
            ):
                raise PassiveTransitionRejected("source report authority changed")
            for result, original in zip(
                source_reports, source_epochs, strict=True,
            ):
                if (
                    type(result) is not UnapprovedSnapshotShapeReview
                    or any(
                        getattr(result, name) is not prior
                        for name, prior in zip(
                            report_fields, original, strict=True,
                        )
                    )
                ):
                    raise PassiveTransitionRejected(
                        "unapproved source report changed during transition"
                    )
            if any(
                getattr(UnapprovedSnapshotShapeReview, name) is not original
                for name, original in zip(
                    source_denials, source_descriptors, strict=True,
                )
            ):
                raise PassiveTransitionRejected("source report authority changed")
            stable()

        stable_source_reports()
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
        descriptors = _ORIGINAL_TRANSITION_DENIALS

        def stable_report() -> None:
            _assert_original_passive_authority()
            if (
                type(report) is not PassiveReadinessTransition
                or any(
                    getattr(report, name) is not prior
                    for name, prior in zip((
                        "before_sha256", "after_sha256",
                        "newly_plausible_paths", "became_unresolved_paths",
                        "newly_malformed_paths", "syntax_repaired_paths",
                        "transition_sha256",
                    ), original, strict=True)
                )
                or any(
                    getattr(PassiveReadinessTransition, n) is not desc
                    for n, desc in zip(_DENIED, descriptors, strict=True)
                )
            ):
                raise PassiveTransitionRejected("passive transition report changed")
            stable_source_reports()

        stable_report()
        for name in _DENIED:
            if getattr(report, name) is not False:
                raise PassiveTransitionRejected("passive transition gained authority")
            stable_report()
        # Re-run both source reviews after reflective denial callbacks.
        # The dataclass __eq__ method is replaceable. Compare the independently
        # validated final reports' exact primitive path/digest fields instead.
        last_before, last_after = inspect(before), inspect(after)
        for later, original_fields in zip(
            (last_before, last_after), source_epochs, strict=True,
        ):
            if any(
                getattr(later, name) != original_value
                for name, original_value in zip(
                    report_fields, original_fields, strict=True,
                )
            ):
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
