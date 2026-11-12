"""Cross-scope privacy-safe expiry receipts never authorize memory deletion."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.memory.expiry_candidate_preview import MemoryExpiryPreview
from ark.memory.expiry_cohort_review import (
    MemoryExpiryCohortRejected,
    aggregate_memory_expiry_cohort,
    compare_memory_expiry_cohorts,
)

_SCOPE_A = "a" * 64
_SCOPE_B = "b" * 64


def _preview(
    scope: str, *, time: int = 100, count: int = 2,
    more: bool = False, identity: str = "c",
) -> MemoryExpiryPreview:
    return MemoryExpiryPreview(
        scope, time, count, more, identity * 64, "d" * 64,
    )


def _review(
    previews: tuple[MemoryExpiryPreview, ...],
    *, expected: tuple[str, ...] = (_SCOPE_A, _SCOPE_B),
    time: int = 100,
):
    return aggregate_memory_expiry_cohort(
        independently_expected_scope_hashes=expected,
        previews=previews,
        asserted_now_ms=time,
    )


def test_aggregates_content_free_counts_without_external_permissions() -> None:
    report = _review((_preview(_SCOPE_A), _preview(_SCOPE_B, count=3, more=True)))
    assert report.scope_hashes == (_SCOPE_A, _SCOPE_B)
    assert report.candidate_count == 5
    assert report.truncated_scopes == (_SCOPE_B,)
    assert len(report.cohort_sha256) == 64
    assert report.deletion_authorized is False
    assert report.cross_scope_atomicity_proven is False
    assert report.independent_custody_proven is False
    assert report.trusted_clock_verified is False


@pytest.mark.parametrize(
    "expected",
    (
        (),
        (_SCOPE_A, _SCOPE_A),
        (_SCOPE_B, _SCOPE_A),
        ("a", _SCOPE_B),
        (_SCOPE_A, "A" * 64),
    ),
)
def test_ambiguous_or_noncanonical_expected_scope_inventory_is_denied(
    expected: tuple[str, ...],
) -> None:
    with pytest.raises(MemoryExpiryCohortRejected):
        _review((_preview(_SCOPE_A), _preview(_SCOPE_B)), expected=expected)


@pytest.mark.parametrize(
    "previews",
    (
        (_preview(_SCOPE_A),),
        (_preview(_SCOPE_B), _preview(_SCOPE_A)),
        (_preview(_SCOPE_A), _preview(_SCOPE_B, time=101)),
        (_preview(_SCOPE_A), _preview(_SCOPE_B, count=-1)),
        (_preview(_SCOPE_A), _preview(_SCOPE_B, count=1001)),
        (_preview(_SCOPE_A), _preview(_SCOPE_B, identity="A")),
        (_preview(_SCOPE_A), _preview(_SCOPE_B, identity="x")),
    ),
)
def test_incomplete_or_inconsistent_expiry_page_rejected(
    previews: tuple[MemoryExpiryPreview, ...],
) -> None:
    with pytest.raises(MemoryExpiryCohortRejected):
        _review(previews)


@pytest.mark.parametrize("now", (True, -1, 2**63, 101))
def test_clock_range_and_type_are_exact(now: object) -> None:
    with pytest.raises(MemoryExpiryCohortRejected):
        _review((_preview(_SCOPE_A), _preview(_SCOPE_B)), time=now)


def test_same_receipt_epoch_reports_only_unchanged_local_claim() -> None:
    a = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    b = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    result = compare_memory_expiry_cohorts(a, b)
    assert result.status == "UNCHANGED_LOCAL_CLAIM"
    assert result.automatic_purge_authorized is False
    assert result.historical_identity_proven is False


def test_mutated_candidate_evidence_is_unverified_not_authorized() -> None:
    a = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    b = _review((_preview(_SCOPE_A), _preview(_SCOPE_B, identity="e")))
    compared = compare_memory_expiry_cohorts(a, b)
    assert compared.status == "CHANGED_UNVERIFIED"
    assert compared.previous_sha256 != compared.observed_sha256


def test_forward_clock_change_is_unverified_even_when_candidate_count_same() -> None:
    first = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    second = _review(
        (_preview(_SCOPE_A, time=101), _preview(_SCOPE_B, time=101)),
        time=101,
    )
    compared = compare_memory_expiry_cohorts(first, second)
    assert compared.status == "CLOCK_ADVANCED_UNVERIFIED"
    assert compared.automatic_purge_authorized is False


def test_clock_rollback_is_denied_before_transition() -> None:
    newer = _review(
        (_preview(_SCOPE_A, time=101), _preview(_SCOPE_B, time=101)),
        time=101,
    )
    older = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    with pytest.raises(MemoryExpiryCohortRejected, match="clock"):
        compare_memory_expiry_cohorts(newer, older)


def test_unrelated_or_missing_scope_claims_cannot_be_joined() -> None:
    a = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    b = _review((_preview(_SCOPE_A),), expected=(_SCOPE_A,))
    with pytest.raises(MemoryExpiryCohortRejected, match="scopes"):
        compare_memory_expiry_cohorts(a, b)


def test_reflected_invalid_digest_is_denied() -> None:
    a = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    bad = replace(a, cohort_sha256="INVALID")
    with pytest.raises(MemoryExpiryCohortRejected):
        compare_memory_expiry_cohorts(a, bad)


def test_truncation_never_disappears_from_cohort_digest() -> None:
    base = _review((_preview(_SCOPE_A), _preview(_SCOPE_B)))
    truncated = _review((_preview(_SCOPE_A), _preview(_SCOPE_B, more=True)))
    assert base.cohort_sha256 != truncated.cohort_sha256
    assert truncated.truncated_scopes == (_SCOPE_B,)
    assert compare_memory_expiry_cohorts(base, truncated).status == "CHANGED_UNVERIFIED"
