"""Content-free restart review of two independently captured Memory expiry cohorts.

A retained summary alone may be edited or stale. Rebuild both epochs from
their supplied per-scope pages and compare a retained prior digest to the
reconstructed image. This is NOT a multi-scope SQLite snapshot, authenticated
clock, consent, or authorization for deletion.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import expiry_cohort_review as cohort_module
from .expiry_candidate_preview import MemoryExpiryPreview
from .expiry_cohort_review import MemoryExpiryCohort

_DOMAIN = b"ARK-memory-expiry-restart-receipt-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_CALLEES = (
    cohort_module.aggregate_memory_expiry_cohort,
    cohort_module.compare_memory_expiry_cohorts,
)
_ORIGINAL_PROTOCOL = (_DOMAIN, _SHA)
_ORIGINAL_HASHLIB_MODULE = hashlib
_ORIGINAL_JSON_MODULE = json
_ORIGINAL_COHORT_MODULE = cohort_module


class MemoryExpiryRestartRejected(ValueError):
    """Retained expiry cohort cannot be reconciled with local page evidence."""


@dataclass(frozen=True, slots=True)
class MemoryExpiryRestartReceipt:
    status: str
    previous_sha256: str
    observed_sha256: str
    candidate_count_before: int
    candidate_count_after: int
    count_delta: int
    truncated_scopes_before: tuple[str, ...]
    truncated_scopes_after: tuple[str, ...]
    receipt_sha256: str

    @property
    def automatic_purge_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def independent_custody_verified(self) -> bool:
        return False

    @property
    def cross_scope_atomicity_proven(self) -> bool:
        return False


_RESULT = MemoryExpiryRestartReceipt
_FIELDS = (
    "status", "previous_sha256", "observed_sha256",
    "candidate_count_before", "candidate_count_after", "count_delta",
    "truncated_scopes_before", "truncated_scopes_after", "receipt_sha256",
    "__init__", "__new__", "__getattribute__", "__getattr__",
    "automatic_purge_authorized", "trusted_clock_verified",
    "independent_custody_verified", "cross_scope_atomicity_proven",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _FIELDS)


def _protocol() -> None:
    if (
        # Check modules before invoking their potentially replaced getters.
        hashlib is not _ORIGINAL_HASHLIB_MODULE
        or json is not _ORIGINAL_JSON_MODULE
        or cohort_module is not _ORIGINAL_COHORT_MODULE
        or _DOMAIN is not _ORIGINAL_PROTOCOL[0]
        or _SHA is not _ORIGINAL_PROTOCOL[1]
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or (
            cohort_module.aggregate_memory_expiry_cohort,
            cohort_module.compare_memory_expiry_cohorts,
        ) != _ORIGINAL_CALLEES
        or MemoryExpiryRestartReceipt is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_FIELDS, _ORIGINAL_RESULT, strict=True)
        )
    ):
        raise MemoryExpiryRestartRejected("expiry restart protocol changed")


def _image(item: MemoryExpiryCohort) -> tuple:
    return (
        item.scope_hashes, item.asserted_now_ms, item.candidate_count,
        item.truncated_scopes, item.cohort_sha256,
    )


def review_memory_expiry_restart_receipt(
    *,
    independently_expected_scope_hashes: tuple[str, ...],
    prior_pages: tuple[MemoryExpiryPreview, ...],
    observed_pages: tuple[MemoryExpiryPreview, ...],
    retained_prior: MemoryExpiryCohort,
    prior_asserted_now_ms: int,
    observed_asserted_now_ms: int,
) -> MemoryExpiryRestartReceipt:
    """Validate a prior retained cohort and new pages; never purge or replay.

    This can detect a tampered retained summary, inconsistent scope/page
    inventory or clock rollback, not whether the independently supplied
    scope inventory itself omitted any scope.
    """
    _protocol()
    if (
        type(independently_expected_scope_hashes) is not tuple
        or type(prior_pages) is not tuple or type(observed_pages) is not tuple
        or type(retained_prior) is not MemoryExpiryCohort
        or type(prior_asserted_now_ms) is not int
        or type(observed_asserted_now_ms) is not int
    ):
        raise MemoryExpiryRestartRejected("inexact expiry restart inputs")
    try:
        previous = cohort_module.aggregate_memory_expiry_cohort(
            independently_expected_scope_hashes=independently_expected_scope_hashes,
            previews=prior_pages,
            asserted_now_ms=prior_asserted_now_ms,
        )
        if _image(retained_prior) != _image(previous):
            raise MemoryExpiryRestartRejected("retained prior cohort differs from pages")
        observed = cohort_module.aggregate_memory_expiry_cohort(
            independently_expected_scope_hashes=independently_expected_scope_hashes,
            previews=observed_pages,
            asserted_now_ms=observed_asserted_now_ms,
        )
        transition = cohort_module.compare_memory_expiry_cohorts(
            previous, observed,
        )
        if (
            transition.previous_sha256 != previous.cohort_sha256
            or transition.observed_sha256 != observed.cohort_sha256
            or transition.automatic_purge_authorized is not False
            or transition.historical_identity_proven is not False
        ):
            raise MemoryExpiryRestartRejected("expiry transition gained authority")

        delta = observed.candidate_count - previous.candidate_count
        encoded = json.dumps(
            (
                independently_expected_scope_hashes, transition.status,
                previous.cohort_sha256, observed.cohort_sha256,
                previous.candidate_count, observed.candidate_count,
                previous.truncated_scopes, observed.truncated_scopes,
            ),
            ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        ).encode("ascii")
        digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
        _protocol()
        # Reconstruct both pages again, to detect changes during review.
        before_again = cohort_module.aggregate_memory_expiry_cohort(
            independently_expected_scope_hashes=independently_expected_scope_hashes,
            previews=prior_pages,
            asserted_now_ms=prior_asserted_now_ms,
        )
        after_again = cohort_module.aggregate_memory_expiry_cohort(
            independently_expected_scope_hashes=independently_expected_scope_hashes,
            previews=observed_pages,
            asserted_now_ms=observed_asserted_now_ms,
        )
        if (
            _image(before_again) != _image(previous)
            or _image(after_again) != _image(observed)
            or _image(retained_prior) != _image(previous)
            or type(digest) is not str or _SHA.fullmatch(digest) is None
        ):
            raise MemoryExpiryRestartRejected("expiry pages changed during review")
    except cohort_module.MemoryExpiryCohortRejected as exc:
        raise MemoryExpiryRestartRejected("expiry cohort rejected") from exc

    result = _RESULT(
        transition.status, previous.cohort_sha256, observed.cohort_sha256,
        previous.candidate_count, observed.candidate_count, delta,
        previous.truncated_scopes, observed.truncated_scopes, digest,
    )
    _protocol()
    if (
        type(result) is not _RESULT
        or result.receipt_sha256 != digest
        or any(
            getattr(result, flag) is not False
            for flag in (
                "automatic_purge_authorized", "trusted_clock_verified",
                "independent_custody_verified", "cross_scope_atomicity_proven",
            )
        )
    ):
        raise MemoryExpiryRestartRejected("expiry restart receipt gained authority")
    return result
