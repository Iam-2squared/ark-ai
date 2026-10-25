"""Untrusted cancellation and claim receipts must retain identity to final return.

Synthetic approval is never verified user consent or live Tool authorization.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_approval_cancellation_fence_review as fence
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationWitness,
)
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim


class NeverExecute:
    def execute(self, call):
        raise AssertionError("offline approval review must not execute")


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _different_equal(value):
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


def _fixture(tmp_path: Path):
    call = ToolCall("offline-tool", "mock-capability", "private", {"fixture": 1})
    registry = ToolRegistry((
        ToolRegistration(
            "offline-tool", "mock-capability", Effect.WRITE,
            "disconnected-backend", NeverExecute(),
        ),
    ))
    claim = make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_digest("issuer"), subject_digest=_digest("subject"),
        purpose_digest=_digest("purpose"), recipient_digest=_digest("recipient"),
        nonce_digest=_digest("nonce"), issued_at_ms=10, expires_at_ms=100,
    )
    ledger = SyntheticCancellationLedger(tmp_path / "cancellation.sqlite")
    return call, registry, claim, ledger


def _review(state):
    call, registry, claim, ledger = state
    return fence.review_synthetic_approval_cancellation_fence(
        claim, registry, call, ledger,
        issuer_digest=claim.issuer_digest, subject_digest=claim.subject_digest,
        purpose_digest=claim.purpose_digest, recipient_digest=claim.recipient_digest,
        now_ms=20, retained=ledger.read_witness(),
    )


@pytest.mark.parametrize("target", ("first_witness", "first_state"))
def test_claim_callback_cannot_replace_initial_receipt(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    original_read = SyntheticCancellationLedger.review_state
    original_claim = fence.review_synthetic_approval_claim
    first = []

    def observed(self, *args, **kwargs):
        result = original_read(self, *args, **kwargs)
        if not first:
            first.append(result)
        return result

    def swapped(*args, **kwargs):
        receipt = original_claim(*args, **kwargs)
        initial = first[0]
        if target == "first_witness":
            object.__setattr__(
                initial.witness, "tail_hash",
                _different_equal(initial.witness.tail_hash),
            )
        else:
            replacement = SyntheticCancellationWitness(
                initial.witness.event_count, initial.witness.tail_hash,
                initial.witness.last_cancelled_at_ms,
            )
            object.__setattr__(initial, "witness", replacement)
        return receipt

    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", observed)
    monkeypatch.setattr(fence, "review_synthetic_approval_claim", swapped)
    with pytest.raises(fence.SyntheticApprovalFenceRejected, match="initial"):
        _review(state)


def test_second_read_cannot_rewrite_claim_receipt(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    original_read = SyntheticCancellationLedger.review_state
    original_claim = fence.review_synthetic_approval_claim
    claimed = []
    count = 0

    def reviewed(*args, **kwargs):
        result = original_claim(*args, **kwargs)
        claimed.append(result)
        return result

    def patched_read(self, *args, **kwargs):
        nonlocal count
        result = original_read(self, *args, **kwargs)
        count += 1
        if count == 2:
            object.__setattr__(
                claimed[0], "bound_action_id",
                _different_equal(claimed[0].bound_action_id),
            )
        return result

    monkeypatch.setattr(fence, "review_synthetic_approval_claim", reviewed)
    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", patched_read)
    with pytest.raises(fence.SyntheticApprovalFenceRejected, match="claim receipt"):
        _review(state)
    assert count == 2


@pytest.mark.parametrize("target", ("final_witness", "receipt"))
def test_final_result_constructor_cannot_rewrite_cancellation_evidence(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    original_read = SyntheticCancellationLedger.review_state
    original_init = fence.SyntheticApprovalFenceReview.__init__
    seen = []

    def recorded(self, *args, **kwargs):
        result = original_read(self, *args, **kwargs)
        seen.append(result)
        return result

    def modified(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if target == "final_witness":
            witness = seen[-1].witness
            object.__setattr__(
                witness, "tail_hash", _different_equal(witness.tail_hash),
            )
        else:
            object.__setattr__(self, "cancellation_event_count", 99)

    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", recorded)
    monkeypatch.setattr(fence.SyntheticApprovalFenceReview, "__init__", modified)
    with pytest.raises(fence.SyntheticApprovalFenceRejected, match="final|result"):
        _review(state)
    assert len(seen) == 2


@pytest.mark.parametrize("target", ("claim", "call"))
def test_first_read_cannot_swap_equal_original_input_carrier(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    original = SyntheticCancellationLedger.review_state

    def mutated(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if target == "claim":
            claim = state[2]
            object.__setattr__(
                claim, "bound_action_id",
                _different_equal(claim.bound_action_id),
            )
        else:
            call = state[0]
            object.__setattr__(
                call, "scope", _different_equal(call.scope),
            )
        return result

    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", mutated)
    with pytest.raises(fence.SyntheticApprovalFenceRejected, match="input|source"):
        _review(state)


def test_unchanged_fence_is_inert_and_preserves_prior_veto(tmp_path):
    state = _fixture(tmp_path)
    review = _review(state)
    assert review.cancellation_event_count == 0
    assert not review.human_consent_verified
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized
