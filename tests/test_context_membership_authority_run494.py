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


def _retained_review(record, veto):
    return review_offline_context_membership(
        (record,),
        expected_record_ids=(record.record_id,),
        owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        scope_vetoes=(veto,),
        observed_at_ms=100,
        max_claim_age_ms=100,
    )


@pytest.mark.parametrize("mutation", ("revocation", "expiry"))
def test_reflected_false_authority_cannot_revive_stale_context(monkeypatch, mutation):
    record = ContextRecordClaim(
        "ctx_" + "1" * 16, "a" * 64, "b" * 64, "c" * 64, 10, 200,
    )
    veto = ContextScopeVetoClaim("b" * 64, False, 50, "d" * 64)

    def adversarial(self):
        if mutation == "revocation":
            object.__setattr__(veto, "revoked", True)
        else:
            object.__setattr__(record, "expires_at_ms", 99)
        return False

    monkeypatch.setattr(
        OfflineContextMembershipReview, "trusted_clock_verified",
        property(adversarial),
    )
    with pytest.raises(OfflineContextAdmissionRejected, match="carrier replaced"):
        _retained_review(record, veto)


def test_reflected_false_authority_cannot_rewrite_result_digest(monkeypatch):
    record = ContextRecordClaim(
        "ctx_" + "1" * 16, "a" * 64, "b" * 64, "c" * 64, 10, 200,
    )
    veto = ContextScopeVetoClaim("b" * 64, False, 50, "d" * 64)

    def adversarial(self):
        object.__setattr__(self, "membership_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        OfflineContextMembershipReview, "trusted_clock_verified",
        property(adversarial),
    )
    with pytest.raises(OfflineContextAdmissionRejected, match="review mutated"):
        _retained_review(record, veto)
