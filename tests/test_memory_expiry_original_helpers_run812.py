"""Memory expiry pages must pass original verifiers before cohort publication."""

from __future__ import annotations

import pytest

import ark.memory.expiry_cohort_review as cohort_module
from ark.memory.expiry_candidate_preview import MemoryExpiryPreview

_SCOPE = "a" * 64


def _page() -> MemoryExpiryPreview:
    return MemoryExpiryPreview(
        _SCOPE, 50, 1, False, "b" * 64, "c" * 64,
    )


def _cohort():
    return cohort_module.aggregate_memory_expiry_cohort(
        independently_expected_scope_hashes=(_SCOPE,),
        previews=(_page(),),
        asserted_now_ms=50,
    )


@pytest.mark.parametrize("replaced", ("_sha", "_image"))
@pytest.mark.parametrize("review", ("aggregate", "compare"))
def test_rebound_expiry_verifier_rejected_without_executing_replacement(
    monkeypatch: pytest.MonkeyPatch, replaced: str, review: str,
) -> None:
    original = _cohort()

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("unreviewed expiry helper was executed")

    with monkeypatch.context() as patch:
        patch.setattr(cohort_module, replaced, forbidden)
        with pytest.raises(
            cohort_module.MemoryExpiryCohortRejected,
            match="evidence contract changed",
        ):
            if review == "aggregate":
                _cohort()
            else:
                cohort_module.compare_memory_expiry_cohorts(original, original)


def test_original_cohort_receipt_remains_content_free_and_non_authorizing() -> None:
    original = _cohort()
    observed = _cohort()
    assert original.cohort_sha256 == observed.cohort_sha256
    assert original.candidate_count == 1
    assert original.deletion_authorized is False
    assert original.trusted_clock_verified is False
    transition = cohort_module.compare_memory_expiry_cohorts(original, observed)
    assert transition.status == "UNCHANGED_LOCAL_CLAIM"
    assert transition.automatic_purge_authorized is False
    assert transition.historical_identity_proven is False
