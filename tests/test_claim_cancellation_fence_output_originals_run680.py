"""An inert durable cancellation veto must not acquire approval authority.

All tests use caller-supplied synthetic identities; no backend, trusted
clock, real consent or global transaction is involved.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_approval_cancellation_fence_review as module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim


class NeverExecute:
    def execute(self, _call):
        raise AssertionError("cancellation review must never dispatch")


@pytest.mark.parametrize(
    "member",
    (
        "approval_id", "bound_action_id", "cancellation_tail_hash",
        "cancellation_event_count", "observed_at_ms",
        "__init__", "__getattribute__", "__getattr__",
        "human_consent_verified", "dispatch_authorized",
        "automatic_replay_authorized",
    ),
)
def test_reflective_result_hook_denied_before_any_cancellation_access(
    monkeypatch, member,
):
    monkeypatch.setattr(
        module.SyntheticApprovalFenceReview, member,
        property(lambda _self: True), raising=False,
    )
    with pytest.raises(
        module.SyntheticApprovalFenceRejected, match="fence output changed",
    ):
        module.review_synthetic_approval_cancellation_fence(
            None, None, None, None,
            issuer_digest="a" * 64, subject_digest="b" * 64,
            purpose_digest="c" * 64, recipient_digest="d" * 64,
            now_ms=20,
        )


def test_exported_veto_review_class_swap_denied_before_sqlite(monkeypatch):
    monkeypatch.setattr(module, "SyntheticApprovalFenceReview", object)
    with pytest.raises(
        module.SyntheticApprovalFenceRejected, match="fence output changed",
    ):
        module.review_synthetic_approval_cancellation_fence(
            None, None, None, None,
            issuer_digest="a" * 64, subject_digest="b" * 64,
            purpose_digest="c" * 64, recipient_digest="d" * 64,
            now_ms=20,
        )


def test_original_veto_result_is_inert_even_with_empty_cancellation_log(
    tmp_path: Path,
):
    call = ToolCall("fixture", "write", "sandbox", {"private": "KEEP-PRIVATE"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverExecute()),
    ))
    digests = {
        name + "_digest": hashlib.sha256(name.encode("ascii")).hexdigest()
        for name in ("issuer", "subject", "purpose", "recipient", "nonce")
    }
    claim = make_synthetic_approval_claim(
        registry, call, **digests, issued_at_ms=10, expires_at_ms=100,
    )
    cancellation = SyntheticCancellationLedger(tmp_path / "cancel.sqlite")
    result = module.review_synthetic_approval_cancellation_fence(
        claim, registry, call, cancellation,
        issuer_digest=digests["issuer_digest"],
        subject_digest=digests["subject_digest"],
        purpose_digest=digests["purpose_digest"],
        recipient_digest=digests["recipient_digest"],
        now_ms=20,
    )
    assert result.cancellation_event_count == 0
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert "KEEP-PRIVATE" not in repr(result)
