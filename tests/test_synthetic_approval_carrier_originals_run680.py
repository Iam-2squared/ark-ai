"""Claim input/output carriers must remain deny-only even under local reflection.

No real issuer, human consent, trusted time, backend invocation or external
authentication is performed by these in-process fixture tests.
"""

import hashlib

import pytest

import ark.agency.synthetic_approval_claim_review as module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, _call):
        raise AssertionError("no synthetic review may invoke a backend")


@pytest.mark.parametrize(
    ("surface", "member"),
    [
        ("envelope", "approval_id"),
        ("envelope", "issuer_digest"),
        ("envelope", "expires_at_ms"),
        ("envelope", "__init__"),
        ("envelope", "__getattribute__"),
        ("envelope", "__getattr__"),
        ("envelope", "dispatch_authorized"),
        ("envelope", "human_consent_verified"),
        ("envelope", "automatic_replay_authorized"),
        ("review", "approval_id"),
        ("review", "bound_action_id"),
        ("review", "observed_at_ms"),
        ("review", "__init__"),
        ("review", "__getattribute__"),
        ("review", "__getattr__"),
        ("review", "dispatch_authorized"),
        ("review", "human_consent_verified"),
        ("review", "automatic_replay_authorized"),
    ],
)
def test_claim_carrier_tampering_denied_before_any_registry_bind(
    monkeypatch, surface, member,
):
    cls = (
        module.SyntheticApprovalEnvelope
        if surface == "envelope" else module.SyntheticApprovalReview
    )
    monkeypatch.setattr(cls, member, property(lambda _self: True), raising=False)
    with pytest.raises(module.SyntheticApprovalRejected, match="carrier changed"):
        module.make_synthetic_approval_claim(
            None, None,
            issuer_digest="a" * 64, subject_digest="b" * 64,
            purpose_digest="c" * 64, recipient_digest="d" * 64,
            nonce_digest="e" * 64, issued_at_ms=10, expires_at_ms=100,
        )
    with pytest.raises(module.SyntheticApprovalRejected, match="carrier changed"):
        module.review_synthetic_approval_claim(
            None, None, None, issuer_digest="a" * 64,
            subject_digest="b" * 64, purpose_digest="c" * 64,
            recipient_digest="d" * 64, now_ms=20, cancelled_ids=frozenset(),
        )


@pytest.mark.parametrize("surface", ("envelope", "review"))
def test_exported_synthetic_carrier_substitution_is_rejected(monkeypatch, surface):
    name = (
        "SyntheticApprovalEnvelope"
        if surface == "envelope" else "SyntheticApprovalReview"
    )
    monkeypatch.setattr(module, name, object)
    with pytest.raises(module.SyntheticApprovalRejected, match="carrier changed"):
        module.make_synthetic_approval_claim(
            None, None,
            issuer_digest="a" * 64, subject_digest="b" * 64,
            purpose_digest="c" * 64, recipient_digest="d" * 64,
            nonce_digest="e" * 64, issued_at_ms=10, expires_at_ms=100,
        )


def test_unmodified_synthetic_claim_keeps_all_authority_denials():
    call = ToolCall("writer", "write", "sandbox", {"private": "DO-NOT-EXPORT"})
    registry = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "fixture", NeverBackend()),
    ))
    digests = {
        name + "_digest": hashlib.sha256(name.encode("ascii")).hexdigest()
        for name in ("issuer", "subject", "purpose", "recipient", "nonce")
    }
    claim = module.make_synthetic_approval_claim(
        registry, call, **digests, issued_at_ms=10, expires_at_ms=100,
    )
    review = module.review_synthetic_approval_claim(
        claim, registry, call,
        **{name: digests[name] for name in (
            "issuer_digest", "subject_digest", "purpose_digest", "recipient_digest",
        )},
        now_ms=20, cancelled_ids=frozenset(),
    )
    assert all(
        getattr(result, name) is False
        for result in (claim, review)
        for name in (
            "dispatch_authorized", "human_consent_verified",
            "automatic_replay_authorized",
        )
    )
    assert "DO-NOT-EXPORT" not in repr(review)
