"""Restart receipts validate both local expiry page epochs, never permit purge."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.memory.expiry_restart_receipt_review as restart
from ark.memory.expiry_candidate_preview import MemoryExpiryPreview
from ark.memory.expiry_cohort_review import aggregate_memory_expiry_cohort

_SCOPE_A = "a" * 64
_SCOPE_B = "b" * 64
_SCOPES = (_SCOPE_A, _SCOPE_B)


def _pages(
    at: int = 100, *, count_b: int = 2, more: bool = False, identity: str = "c",
):
    return (
        MemoryExpiryPreview(_SCOPE_A, at, 1, False, "d" * 64, "e" * 64),
        MemoryExpiryPreview(_SCOPE_B, at, count_b, more, identity * 64, "f" * 64),
    )


def _inputs():
    before = _pages()
    retained = aggregate_memory_expiry_cohort(
        independently_expected_scope_hashes=_SCOPES,
        previews=before,
        asserted_now_ms=100,
    )
    return {
        "independently_expected_scope_hashes": _SCOPES,
        "prior_pages": before,
        "observed_pages": _pages(),
        "retained_prior": retained,
        "prior_asserted_now_ms": 100,
        "observed_asserted_now_ms": 100,
    }


def test_unmodified_restart_cohort_receipt_is_content_free_and_inert() -> None:
    inputs = _inputs()
    report = restart.review_memory_expiry_restart_receipt(**inputs)
    assert report == restart.review_memory_expiry_restart_receipt(**inputs)
    assert report.status == "UNCHANGED_LOCAL_CLAIM"
    assert report.previous_sha256 == report.observed_sha256
    assert report.candidate_count_before == 3
    assert report.candidate_count_after == 3
    assert report.count_delta == 0
    assert report.truncated_scopes_before == ()
    assert report.truncated_scopes_after == ()
    assert len(report.receipt_sha256) == 64
    assert report.automatic_purge_authorized is False
    assert report.trusted_clock_verified is False
    assert report.independent_custody_verified is False
    assert report.cross_scope_atomicity_proven is False


@pytest.mark.parametrize(
    ("changed", "status", "delta"),
    (
        ("count-up", "CHANGED_UNVERIFIED", 2),
        ("count-down", "CHANGED_UNVERIFIED", -1),
        ("has-more", "CHANGED_UNVERIFIED", 0),
        ("page-digest", "CHANGED_UNVERIFIED", 0),
        ("clock-advance", "CLOCK_ADVANCED_UNVERIFIED", 0),
    ),
)
def test_only_explicit_unverified_differences_are_reported(
    changed: str, status: str, delta: int,
) -> None:
    inputs = _inputs()
    if changed == "count-up":
        inputs["observed_pages"] = _pages(count_b=4)
    elif changed == "count-down":
        inputs["observed_pages"] = _pages(count_b=1)
    elif changed == "has-more":
        inputs["observed_pages"] = _pages(more=True)
    elif changed == "page-digest":
        inputs["observed_pages"] = _pages(identity="0")
    elif changed == "clock-advance":
        inputs["observed_pages"] = _pages(at=101)
        inputs["observed_asserted_now_ms"] = 101
    report = restart.review_memory_expiry_restart_receipt(**inputs)
    assert report.status == status
    assert report.count_delta == delta
    assert report.previous_sha256 != report.observed_sha256
    if changed == "has-more":
        assert report.truncated_scopes_after == (_SCOPE_B,)
    assert report.automatic_purge_authorized is False


@pytest.mark.parametrize(
    "damage",
    (
        "forged-retained-digest", "forged-retained-count", "forged-retained-truncation",
        "mismatched-prior-page", "mismatched-observed-page",
        "prior-scope-swapped", "missing-observed", "missing-inventory",
        "duplicate-scope", "wrong-scope-order", "new-unexpected-scope",
        "negative-count", "zero-truncated", "bad-page-digest", "clock-rollback",
        "clock-disagreement", "bool-time", "oversized-time", "inexact-page",
    ),
)
def test_restart_refuses_stale_or_incoherent_cohort_evidence(damage: str) -> None:
    inputs = _inputs()
    if damage == "forged-retained-digest":
        inputs["retained_prior"] = replace(inputs["retained_prior"], cohort_sha256="0" * 64)
    elif damage == "forged-retained-count":
        inputs["retained_prior"] = replace(inputs["retained_prior"], candidate_count=10)
    elif damage == "forged-retained-truncation":
        inputs["retained_prior"] = replace(
            inputs["retained_prior"], truncated_scopes=(_SCOPE_B,),
        )
    elif damage == "mismatched-prior-page":
        inputs["prior_pages"] = _pages(identity="0")
    elif damage == "mismatched-observed-page":
        inputs["observed_pages"] = _pages(at=101)
    elif damage == "prior-scope-swapped":
        inputs["prior_pages"] = tuple(reversed(inputs["prior_pages"]))
    elif damage == "missing-observed":
        inputs["observed_pages"] = inputs["observed_pages"][:1]
    elif damage == "missing-inventory":
        inputs["independently_expected_scope_hashes"] = ()
    elif damage == "duplicate-scope":
        inputs["independently_expected_scope_hashes"] = (_SCOPE_A, _SCOPE_A)
    elif damage == "wrong-scope-order":
        inputs["independently_expected_scope_hashes"] = tuple(reversed(_SCOPES))
    elif damage == "new-unexpected-scope":
        inputs["independently_expected_scope_hashes"] = (_SCOPE_A, "0" * 64)
    elif damage == "negative-count":
        inputs["observed_pages"] = _pages(count_b=-1)
    elif damage == "zero-truncated":
        inputs["observed_pages"] = _pages(count_b=0, more=True)
    elif damage == "bad-page-digest":
        page = inputs["observed_pages"][1]
        inputs["observed_pages"] = (
            inputs["observed_pages"][0], replace(page, candidate_sha256="X" * 64),
        )
    elif damage == "clock-rollback":
        inputs["observed_pages"] = _pages(at=99)
        inputs["observed_asserted_now_ms"] = 99
    elif damage == "clock-disagreement":
        inputs["observed_asserted_now_ms"] = 101
    elif damage == "bool-time":
        inputs["observed_asserted_now_ms"] = True
    elif damage == "oversized-time":
        inputs["observed_asserted_now_ms"] = 1 << 63
    elif damage == "inexact-page":
        inputs["prior_pages"] = (inputs["prior_pages"][0], object())
    with pytest.raises(restart.MemoryExpiryRestartRejected):
        restart.review_memory_expiry_restart_receipt(**inputs)


@pytest.mark.parametrize("damage", ("rebound-aggregator", "authorizing-result"))
def test_replacement_before_page_read_cannot_bypass_original_authority(
    monkeypatch: pytest.MonkeyPatch, damage: str,
) -> None:
    inputs = _inputs()
    with monkeypatch.context() as patch:
        if damage == "rebound-aggregator":
            patch.setattr(
                restart.cohort_module, "aggregate_memory_expiry_cohort",
                lambda **kwargs: (_ for _ in ()).throw(
                    AssertionError("substituted verifier executed")
                ),
            )
        else:
            patch.setattr(
                restart.MemoryExpiryRestartReceipt,
                "automatic_purge_authorized",
                property(lambda _: True),
            )
        with pytest.raises(restart.MemoryExpiryRestartRejected, match="protocol changed"):
            restart.review_memory_expiry_restart_receipt(**inputs)
