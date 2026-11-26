"""A caller's authority claims cannot alter original Python safety hooks.

These checks are disconnected, deny-only metadata; no real authorization or
trusted clock is acquired, even when all caller claims match.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.agency import synthetic_authority_boundary_review as review


def _claims():
    return review.SyntheticAuthorityClaims(
        "issuer", "subject", "tools_" + "a" * 64,
        "bound_" + "b" * 64, "c" * 64, 100, 200,
    )


def _observations():
    return review.SyntheticAuthorityObservations(*(["unknown"] * 6))


@pytest.mark.parametrize(
    "changed",
    ("claim_slot", "observation_slot", "report_constructor",
     "report_denial", "claim_lookup"),
)
def test_substituted_field_or_constructor_is_rejected_before_execution(
    monkeypatch, changed,
):
    claims, observations = _claims(), _observations()
    called = []

    def forbidden(*_args, **_kwargs):
        called.append(changed)
        raise AssertionError("forged getter/constructor executed")

    if changed == "claim_slot":
        monkeypatch.setattr(
            review.SyntheticAuthorityClaims, "issuer_claim", property(forbidden),
        )
    elif changed == "observation_slot":
        monkeypatch.setattr(
            review.SyntheticAuthorityObservations,
            "human_consent", property(forbidden),
        )
    elif changed == "report_constructor":
        monkeypatch.setattr(
            review.SyntheticAuthorityGapReport, "__init__", forbidden,
        )
    elif changed == "report_denial":
        monkeypatch.setattr(
            review.SyntheticAuthorityGapReport,
            "dispatch_authorized", property(forbidden),
        )
    else:
        monkeypatch.setattr(
            review.SyntheticAuthorityClaims, "__getattribute__", forbidden,
        )

    with pytest.raises(
        review.SyntheticAuthorityRejected,
        match="constructor or field hooks changed",
    ):
        review.review_synthetic_authority_gaps(claims, observations)
    assert called == []


def test_hash_callback_cannot_install_forged_report_constructor(
    monkeypatch,
):
    claims, observations = _claims(), _observations()
    native = review.hashlib.sha256
    called = []

    def forged(*_args, **_kwargs):
        called.append("forged")
        raise AssertionError("report constructor executed")

    def reentrant(payload):
        monkeypatch.setattr(
            review.SyntheticAuthorityGapReport, "__init__", forged,
        )
        return native(payload)

    monkeypatch.setattr(review, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(
        review.SyntheticAuthorityRejected,
        match="digest or parser dependencies changed",
    ):
        review.review_synthetic_authority_gaps(claims, observations)
    assert called == []


def test_original_authority_report_remains_deny_only():
    result = review.review_synthetic_authority_gaps(_claims(), _observations())
    assert len(result.blockers) == 6
    assert result.issuer_authenticated is False
    assert result.clock_authenticated is False
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
