"""Impossible expiry pagination cannot become a content-free cohort witness."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.memory.expiry_candidate_preview import MemoryExpiryPreview
from ark.memory.expiry_cohort_review import (
    MemoryExpiryCohortRejected,
    aggregate_memory_expiry_cohort,
    compare_memory_expiry_cohorts,
)

_A = "a" * 64
_B = "b" * 64


def _page(scope: str, *, count: int = 1, more: bool = False) -> MemoryExpiryPreview:
    return MemoryExpiryPreview(scope, 10, count, more, "c" * 64, "d" * 64)


def _cohort(*pages: MemoryExpiryPreview):
    return aggregate_memory_expiry_cohort(
        independently_expected_scope_hashes=(_A, _B),
        previews=pages,
        asserted_now_ms=10,
    )


def test_empty_untruncated_pages_and_nonempty_truncated_pages_remain_inert() -> None:
    cohort = _cohort(_page(_A, count=0), _page(_B, count=1, more=True))
    assert cohort.candidate_count == 1
    assert cohort.truncated_scopes == (_B,)
    assert cohort.deletion_authorized is False
    assert cohort.trusted_clock_verified is False
    assert compare_memory_expiry_cohorts(cohort, cohort).automatic_purge_authorized is False


@pytest.mark.parametrize(
    ("zero_scope", "other_count"),
    ((_A, 0), (_B, 1), (_A, 5), (_B, 0)),
)
def test_overflow_claim_with_zero_visible_candidates_is_impossible(
    zero_scope: str, other_count: int,
) -> None:
    a = _page(_A, count=other_count if zero_scope == _B else 0,
              more=zero_scope == _A)
    b = _page(_B, count=other_count if zero_scope == _A else 0,
              more=zero_scope == _B)
    with pytest.raises(MemoryExpiryCohortRejected, match="unbounded or authorizing"):
        _cohort(a, b)


@pytest.mark.parametrize(
    ("count", "truncated"),
    (
        (0, (_A,)),
        (0, (_A, _B)),
        (1, (_A, _B)),
        (0, (_B,)),
    ),
)
def test_forged_retained_cohort_cannot_claim_more_truncated_scopes_than_rows(
    count: int, truncated: tuple[str, ...],
) -> None:
    original = _cohort(_page(_A), _page(_B))
    forged = replace(original, candidate_count=count, truncated_scopes=truncated)
    with pytest.raises(MemoryExpiryCohortRejected, match="invalid retained"):
        compare_memory_expiry_cohorts(original, forged)
