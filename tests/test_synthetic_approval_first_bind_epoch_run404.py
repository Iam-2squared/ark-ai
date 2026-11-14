"""Claim construction and review refuse self-consistent first-bind substitution.

A synthetic approval digest cannot authenticate an issuer, trusted clock or
human consent, and this entire module never dispatches a ToolBackend.
"""

import hashlib

import pytest

import ark.agency.synthetic_approval_claim_review as claim_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, _call):
        raise AssertionError("claim tests must never dispatch a backend")


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _fixture():
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "never", NeverExecute()),
    ))
    call = ToolCall("writer", "fixture.write", "original", {"v": 1})
    return registry, call


def _make(registry, call):
    return claim_module.make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_digest("issuer"),
        subject_digest=_digest("subject"),
        purpose_digest=_digest("purpose"),
        recipient_digest=_digest("recipient"),
        nonce_digest=_digest("nonce"),
        issued_at_ms=10,
        expires_at_ms=100,
    )


def _review(envelope, registry, call):
    return claim_module.review_synthetic_approval_claim(
        envelope, registry, call,
        issuer_digest=envelope.issuer_digest,
        subject_digest=envelope.subject_digest,
        purpose_digest=envelope.purpose_digest,
        recipient_digest=envelope.recipient_digest,
        now_ms=20, cancelled_ids=frozenset(),
    )


def _mutate(call, field):
    replacement = "substituted" if field == "scope" else {"v": 2}
    object.__setattr__(call, field, replacement)


@pytest.mark.parametrize("phase", (1, 2))
@pytest.mark.parametrize("field", ("scope", "arguments"))
def test_claim_constructor_refuses_reflected_change_after_registry_bind(
    monkeypatch, phase, field,
):
    registry, call = _fixture()
    original = ToolRegistry.bind
    seen = []

    def swapped(self, action):
        bound = original(self, action)
        if self is registry:
            seen.append(bound)
            if len(seen) == phase:
                _mutate(call, field)
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", swapped)
    with pytest.raises(
        claim_module.SyntheticApprovalRejected,
        match="input changed during construction",
    ):
        _make(registry, call)
    assert len(seen) == phase


@pytest.mark.parametrize("phase", (1, 2))
@pytest.mark.parametrize("field", ("scope", "arguments"))
def test_claim_review_refuses_changed_action_after_registry_bind(
    monkeypatch, phase, field,
):
    registry, call = _fixture()
    envelope = _make(registry, call)
    original = ToolRegistry.bind
    seen = []

    def swapped(self, action):
        bound = original(self, action)
        if self is registry:
            seen.append(bound)
            if len(seen) == phase:
                _mutate(call, field)
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", swapped)
    with pytest.raises(
        claim_module.SyntheticApprovalRejected,
        match="approval review input changed",
    ):
        _review(envelope, registry, call)
    assert len(seen) == phase


def test_initial_claim_validation_cannot_replace_prior_envelope(
    monkeypatch,
):
    registry, call = _fixture()
    envelope = _make(registry, call)
    original = claim_module._validate
    seen = []

    def validate(item):
        original(item)
        if item is envelope:
            seen.append(1)
            object.__setattr__(envelope, "expires_at_ms", 101)

    monkeypatch.setattr(claim_module, "_validate", validate)
    with pytest.raises(
        claim_module.SyntheticApprovalRejected,
        match="review input changed",
    ):
        _review(envelope, registry, call)
    assert seen == [1]


def test_constructor_rejects_identity_hash_callback_that_mutates_action(
    monkeypatch,
):
    registry, call = _fixture()
    original = claim_module._identity
    seen = []

    def mutate_during_hash(fields):
        result = original(fields)
        seen.append(1)
        if len(seen) == 1:
            object.__setattr__(call, "scope", "retargeted")
        return result

    monkeypatch.setattr(claim_module, "_identity", mutate_during_hash)
    with pytest.raises(
        claim_module.SyntheticApprovalRejected,
        match="input changed during construction",
    ):
        _make(registry, call)
    assert seen == [1]


def test_stable_claim_and_review_still_never_authorize(tmp_path):
    registry, call = _fixture()
    original_request = call.request_id
    envelope = _make(registry, call)
    review = _review(envelope, registry, call)
    assert envelope.request_id == original_request
    assert not envelope.human_consent_verified
    assert not envelope.dispatch_authorized
    assert not review.human_consent_verified
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized
