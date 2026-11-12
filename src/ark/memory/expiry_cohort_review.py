"""Content-free cross-scope Memory expiry cohort and restart comparison.

This opt-in reviewer accepts independently retained, synthetic digest receipts.
It never opens SQLite, reads memory content, deletes, invokes purge_expired,
certifies a trusted clock, or proves snapshots across scopes are atomic.
Even a complete-looking page may be stale by the time a caller uses it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .expiry_candidate_preview import MemoryExpiryPreview

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-memory-expiry-cohort-review-v1\0"
_MAX_SCOPES = 64
_MAX_CANDIDATES = 64_000
_MAX_TIME = (1 << 63) - 1


class MemoryExpiryCohortRejected(ValueError):
    """No bounded, unambiguous non-authorizing expiry cohort can be formed."""


@dataclass(frozen=True, slots=True)
class MemoryExpiryCohort:
    scope_hashes: tuple[str, ...]
    asserted_now_ms: int
    candidate_count: int
    truncated_scopes: tuple[str, ...]
    cohort_sha256: str

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def cross_scope_atomicity_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class MemoryExpiryCohortTransition:
    status: str
    previous_sha256: str
    observed_sha256: str

    @property
    def automatic_purge_authorized(self) -> bool:
        return False

    @property
    def historical_identity_proven(self) -> bool:
        return False


_PREVIEW = MemoryExpiryPreview
_COHORT = MemoryExpiryCohort
_TRANSITION = MemoryExpiryCohortTransition
_PREVIEW_FIELDS = (
    "scope_sha256", "read_at_ms", "candidate_count", "has_more",
    "candidate_sha256", "preview_sha256",
)
_PREVIEW_DENIALS = (
    "deletion_authorized", "physical_erasure_proven",
    "owner_consent_authenticated", "trusted_clock_verified",
    "external_disclosure_authorized",
)
_COHORT_DENIALS = (
    "deletion_authorized", "cross_scope_atomicity_proven",
    "independent_custody_proven", "trusted_clock_verified",
)
_TRANSITION_DENIALS = ("automatic_purge_authorized", "historical_identity_proven")
_ORIGINAL_PREVIEW = tuple(
    vars(_PREVIEW).get(name) for name in _PREVIEW_FIELDS + _PREVIEW_DENIALS
)
_ORIGINAL_COHORT = tuple(
    vars(_COHORT).get(name) for name in (
        "scope_hashes", "asserted_now_ms", "candidate_count", "truncated_scopes",
        "cohort_sha256", "__init__", *_COHORT_DENIALS,
    )
)
_ORIGINAL_TRANSITION = tuple(
    vars(_TRANSITION).get(name) for name in (
        "status", "previous_sha256", "observed_sha256", "__init__",
        *_TRANSITION_DENIALS,
    )
)
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
# Keep the digest algorithm, wire domain, resource budgets and carrier layout
# pinned across the whole read-only review. A rebound regex must not let a
# forged scope digest or cohort digest be treated as well formed.
_ORIGINAL_MODULES = (hashlib, json, re)
_ORIGINAL_PROTOCOL = (_SHA, _DOMAIN, _MAX_SCOPES, _MAX_CANDIDATES, _MAX_TIME)
_ORIGINAL_TYPES = (MemoryExpiryPreview, MemoryExpiryCohort, MemoryExpiryCohortTransition)
_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_HOOKS = tuple(
    tuple(vars(cls).get(name) for name in _HOOKS)
    for cls in _ORIGINAL_TYPES
)


def _protocol() -> None:
    if (
        (hashlib, json, re) != _ORIGINAL_MODULES
        or (_SHA is not _ORIGINAL_PROTOCOL[0])
        or (_DOMAIN is not _ORIGINAL_PROTOCOL[1])
        or any(type(value) is not int for value in (
            _MAX_SCOPES, _MAX_CANDIDATES, _MAX_TIME,
        ))
        or (_MAX_SCOPES, _MAX_CANDIDATES, _MAX_TIME) != _ORIGINAL_PROTOCOL[2:]
        or (MemoryExpiryPreview, MemoryExpiryCohort, MemoryExpiryCohortTransition)
        != _ORIGINAL_TYPES
        or any(
            vars(cls).get(name) is not old
            for cls, values in zip(_ORIGINAL_TYPES, _ORIGINAL_HOOKS, strict=True)
            for name, old in zip(_HOOKS, values, strict=True)
        )
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or any(
            vars(cls).get(name) is not old
            for cls, names, old_values in (
                (_PREVIEW, _PREVIEW_FIELDS + _PREVIEW_DENIALS, _ORIGINAL_PREVIEW),
                (_COHORT, (
                    "scope_hashes", "asserted_now_ms", "candidate_count",
                    "truncated_scopes", "cohort_sha256", "__init__",
                    *_COHORT_DENIALS,
                ), _ORIGINAL_COHORT),
                (_TRANSITION, (
                    "status", "previous_sha256", "observed_sha256",
                    "__init__", *_TRANSITION_DENIALS,
                ), _ORIGINAL_TRANSITION),
            )
            for name, old in zip(names, old_values, strict=True)
        )
    ):
        raise MemoryExpiryCohortRejected("expiry cohort evidence contract changed")


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _image(report: MemoryExpiryPreview) -> tuple[str, int, int, bool, str, str]:
    _protocol()
    if type(report) is not _PREVIEW:
        raise MemoryExpiryCohortRejected("exact expiry preview required")
    image = (
        report.scope_sha256, report.read_at_ms, report.candidate_count,
        report.has_more, report.candidate_sha256, report.preview_sha256,
    )
    if (
        not _sha(image[0]) or type(image[1]) is not int
        or not 0 <= image[1] <= _MAX_TIME
        or type(image[2]) is not int or not 0 <= image[2] <= 1000
        or type(image[3]) is not bool or (image[3] and image[2] == 0)
        or not _sha(image[4]) or not _sha(image[5])
        or any(getattr(report, name) is not False for name in _PREVIEW_DENIALS)
    ):
        raise MemoryExpiryCohortRejected("unbounded or authorizing expiry preview")
    _protocol()
    return image


def aggregate_memory_expiry_cohort(
    *,
    independently_expected_scope_hashes: tuple[str, ...],
    previews: tuple[MemoryExpiryPreview, ...],
    asserted_now_ms: int,
) -> MemoryExpiryCohort:
    """Bind one bounded, exact scope inventory to opaque expiry page receipts.

    Retained names must come from a source independent of these pages. Page
    truncation is exposed explicitly rather than silently treated as coverage.
    No local digest can prove completeness or prevent post-check TOCTOU.
    """
    _protocol()
    expected = independently_expected_scope_hashes
    if (
        type(expected) is not tuple or not 1 <= len(expected) <= _MAX_SCOPES
        or any(not _sha(item) for item in expected)
        or expected != tuple(sorted(set(expected)))
        or type(previews) is not tuple or len(previews) != len(expected)
        or type(asserted_now_ms) is not int
        or not 0 <= asserted_now_ms <= _MAX_TIME
    ):
        raise MemoryExpiryCohortRejected("invalid independent expiry scope inventory")

    pinned = tuple((item, _image(item)) for item in previews)

    def stable() -> None:
        _protocol()
        if any(
            type(item) is not _PREVIEW or _image(item) != fields
            or any(
                now is not old for now, old in zip(
                    (
                        item.scope_sha256, item.read_at_ms, item.candidate_count,
                        item.has_more, item.candidate_sha256, item.preview_sha256,
                    ), fields, strict=True,
                )
            )
            for item, fields in pinned
        ):
            raise MemoryExpiryCohortRejected("expiry cohort receipt changed")

    images = tuple(image for _, image in pinned)
    if any(
        image[0] != name or image[1] != asserted_now_ms
        for name, image in zip(expected, images, strict=True)
    ):
        raise MemoryExpiryCohortRejected("scope or clock mismatch across expiry pages")
    total = sum(image[2] for image in images)
    if total > _MAX_CANDIDATES:
        raise MemoryExpiryCohortRejected("expiry cohort candidate budget exceeded")
    truncated = tuple(image[0] for image in images if image[3])
    stable()
    encoded = json.dumps(
        (expected, asserted_now_ms, images), ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    report = _COHORT(expected, asserted_now_ms, total, truncated, digest)
    _protocol()
    if (
        type(report) is not _COHORT
        or report.scope_hashes is not expected
        or report.candidate_count != total
        or report.truncated_scopes != truncated
        or report.cohort_sha256 != digest
        or any(getattr(report, name) is not False for name in _COHORT_DENIALS)
    ):
        raise MemoryExpiryCohortRejected("expiry cohort result changed")
    stable()
    return report


def compare_memory_expiry_cohorts(
    prior: MemoryExpiryCohort,
    observed: MemoryExpiryCohort,
) -> MemoryExpiryCohortTransition:
    """Compare opaque local cohort claims without treating them as purge grants."""
    _protocol()
    if type(prior) is not _COHORT or type(observed) is not _COHORT:
        raise MemoryExpiryCohortRejected("exact expiry cohorts required")

    def checked(item: MemoryExpiryCohort) -> tuple[tuple[str, ...], int, int, tuple[str, ...], str]:
        if (
            type(item.scope_hashes) is not tuple
            or not 1 <= len(item.scope_hashes) <= _MAX_SCOPES
            or item.scope_hashes != tuple(sorted(set(item.scope_hashes)))
            or any(not _sha(name) for name in item.scope_hashes)
            or type(item.asserted_now_ms) is not int
            or not 0 <= item.asserted_now_ms <= _MAX_TIME
            or type(item.candidate_count) is not int
            or not 0 <= item.candidate_count <= _MAX_CANDIDATES
            or type(item.truncated_scopes) is not tuple
            or any(name not in item.scope_hashes for name in item.truncated_scopes)
            or item.truncated_scopes != tuple(sorted(set(item.truncated_scopes)))
            # Each truncated scope contains at least one observed candidate.
            # A cohort claiming fewer candidates than truncated pages cannot
            # come from aggregate_memory_expiry_cohort at any permitted limit.
            or item.candidate_count < len(item.truncated_scopes)
            or not _sha(item.cohort_sha256)
            or any(getattr(item, name) is not False for name in _COHORT_DENIALS)
        ):
            raise MemoryExpiryCohortRejected("invalid retained expiry cohort")
        return (
            item.scope_hashes, item.asserted_now_ms, item.candidate_count,
            item.truncated_scopes, item.cohort_sha256,
        )

    a, b = checked(prior), checked(observed)
    if a[0] != b[0] or b[1] < a[1]:
        raise MemoryExpiryCohortRejected("expiry scopes changed or clock regressed")
    if b[1] > a[1]:
        status = "CLOCK_ADVANCED_UNVERIFIED"
    elif a == b:
        status = "UNCHANGED_LOCAL_CLAIM"
    else:
        status = "CHANGED_UNVERIFIED"
    _protocol()
    result = _TRANSITION(status, a[4], b[4])
    if (
        type(result) is not _TRANSITION
        or result.status != status or result.previous_sha256 != a[4]
        or result.observed_sha256 != b[4]
        or any(getattr(result, name) is not False for name in _TRANSITION_DENIALS)
    ):
        raise MemoryExpiryCohortRejected("expiry cohort transition gained authority")
    _protocol()
    if checked(prior) != a or checked(observed) != b:
        raise MemoryExpiryCohortRejected("expiry cohort changed during comparison")
    return result
