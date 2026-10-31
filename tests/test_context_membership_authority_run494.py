"""Context metadata review must never become consent, disclosure or time proof."""

from __future__ import annotations

import pytest

from ark.offline_context_membership_guard import (
    ContextRecordClaim,
    ContextScopeVetoClaim,
    OfflineContextAdmissionRejected,
    OfflineContextMembershipReview,
    review_offline_context_membership,
)


def _review():
    scope = "b" * 64
    return review_offline_context_membership(
        (ContextRecordClaim("ctx_" + "1" * 16, "a" * 64, scope,
                            "c" * 64, 10, 200),),
        expected_record_ids=("ctx_" + "1" * 16,),
        owner_digest="a" * 64,
        allowed_scope_digests=(scope,),
        scope_vetoes=(
            ContextScopeVetoClaim(scope, False, 50, "d" * 64),
        ),
        observed_at_ms=100,
        max_claim_age_ms=100,
    )


@pytest.mark.parametrize(
    "flag",
    (
        "consent_verified",
        "disclosure_authorized",
        "retention_authorized",
        "trusted_clock_verified",
    ),
)
def test_reflective_permission_on_exact_result_is_denied(monkeypatch, flag):
    monkeypatch.setattr(
        OfflineContextMembershipReview, flag, property(lambda self: True),
    )
    with pytest.raises(
        OfflineContextAdmissionRejected, match="admission review mutated",
    ):
        _review()


def test_diagnostic_remains_inert_without_plaintext():
    report = _review()
    assert report.record_count == 1
    assert len(report.membership_sha256) == 64
    assert report.consent_verified is False
    assert report.disclosure_authorized is False
    assert report.retention_authorized is False
    assert report.trusted_clock_verified is False
    assert not hasattr(report, "content")
