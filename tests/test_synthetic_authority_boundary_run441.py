"""Run441: disconnected authority is never trusted or actionable."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark.agency import synthetic_authority_boundary_review as mod


@pytest.fixture
def claims():
    return mod.SyntheticAuthorityClaims(
        "issuer-a", "subject-a", "tools_" + "a" * 64,
        "bound_" + "b" * 64, "c" * 64, 100, 200,
    )


@pytest.fixture
def observations():
    return mod.SyntheticAuthorityObservations(*(["unknown"] * 6))


def test_unknown_evidence_never_authorizes(claims, observations):
    review = mod.review_synthetic_authority_gaps(claims, observations)
    assert len(review.blockers) == 6
    assert all(word.endswith("_unverified") for word in review.blockers)
    assert not any((review.dispatch_authorized, review.automatic_replay_authorized,
                    review.issuer_authenticated, review.clock_authenticated,
                    review.human_consent_verified, review.external_outcome_known))


def test_all_caller_claimed_never_authorizes(claims):
    review = mod.review_synthetic_authority_gaps(
        claims, mod.SyntheticAuthorityObservations(*(["caller_claimed"] * 6)),
    )
    assert len(review.blockers) == 6
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized
    assert not review.external_outcome_known


def test_retained_local_digest_detects_drift(claims, observations):
    first = mod.review_synthetic_authority_gaps(claims, observations)
    assert mod.review_synthetic_authority_gaps(
        claims, observations, retained_claim_digest=first.claim_digest,
    ) == first
    with pytest.raises(mod.SyntheticAuthorityRejected):
        mod.review_synthetic_authority_gaps(
            replace(claims, expires_at_ms=201), observations,
            retained_claim_digest=first.claim_digest,
        )


@pytest.mark.parametrize("field,value", [
    ("issuer_claim", ""), ("subject_claim", "../scope"),
    ("issuer_claim", "x" * 129), ("registry_revision", "tools_nothex"),
    ("bound_action_id", "bound_123"), ("occurrence_digest", "nothex"),
    ("issued_at_ms", True), ("issued_at_ms", -1),
    ("expires_at_ms", 100), ("expires_at_ms", 2**63),
])
def test_rejects_invalid_claims(claims, observations, field, value):
    with pytest.raises(mod.SyntheticAuthorityRejected):
        mod.review_synthetic_authority_gaps(replace(claims, **{field: value}), observations)


@pytest.mark.parametrize("field,value", [
    ("issuer_signature", "verified"), ("trusted_clock", True),
    ("human_consent", "trusted"), ("preaction_audit", None),
    ("occurrence_replay_fence", ""), ("external_result", "executed"),
])
def test_caller_cannot_mark_proofs_verified(claims, observations, field, value):
    with pytest.raises(mod.SyntheticAuthorityRejected):
        mod.review_synthetic_authority_gaps(claims, replace(observations, **{field: value}))


def test_mutated_claim_during_hash_fails_closed(claims, observations, monkeypatch):
    original = mod.hashlib.sha256
    def reentrant(value):
        object.__setattr__(claims, "issuer_claim", "issuer-b")
        return original(value)
    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.SyntheticAuthorityRejected, match="changed"):
        mod.review_synthetic_authority_gaps(claims, observations)


def test_mutated_probe_during_hash_fails_closed(claims, observations, monkeypatch):
    original = mod.hashlib.sha256
    def reentrant(value):
        object.__setattr__(observations, "preaction_audit", "caller_claimed")
        return original(value)
    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.SyntheticAuthorityRejected, match="changed"):
        mod.review_synthetic_authority_gaps(claims, observations)


def test_exact_types_and_retained_hash(claims, observations):
    for bad in (object(), None, True):
        with pytest.raises(mod.SyntheticAuthorityRejected):
            mod.review_synthetic_authority_gaps(bad, observations)
        with pytest.raises(mod.SyntheticAuthorityRejected):
            mod.review_synthetic_authority_gaps(claims, bad)
    with pytest.raises(mod.SyntheticAuthorityRejected):
        mod.review_synthetic_authority_gaps(claims, observations, retained_claim_digest="NO")
