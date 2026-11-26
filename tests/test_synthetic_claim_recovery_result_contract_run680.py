"""Synthetic WRITE recovery cannot return a reflection-modified authority receipt.

All tests are disconnected: no SQLite, backend execution or real approval.
The diagnostic's output must retain original fields, construction and denials.
"""

import pytest

import ark.agency.synthetic_claim_recovery_review as module


@pytest.mark.parametrize(
    "member",
    [
        "approval_id",
        "registry_revision",
        "bound_action_id",
        "request_id",
        "step_id",
        "step_state",
        "ambiguous_write",
        "matching_occurrences",
        "cancellation_event_count",
        "cancellation_tail_hash",
        "observed_at_ms",
        "__init__",
        "__getattribute__",
        "__getattr__",
        "human_consent_verified",
        "dispatch_authorized",
        "automatic_replay_authorized",
        "external_outcome_known",
    ],
)
def test_result_contract_patch_rejected_before_private_store_access(monkeypatch, member):
    executed = []

    def forbidden(*_args, **_kwargs):
        executed.append(True)
        raise AssertionError("private store/approval callback must not run")

    monkeypatch.setattr(
        module, "review_synthetic_approval_cancellation_fence", forbidden,
    )
    monkeypatch.setattr(
        module.SyntheticClaimRecoveryReview, member,
        property(lambda _self: True), raising=False,
    )
    with pytest.raises(
        module.SyntheticClaimRecoveryRejected,
        match="result contract changed",
    ):
        module.review_synthetic_claim_write_recovery(
            None, None, None, None, None, None, None,
            step_id="fixture", issuer_digest="0" * 64,
            subject_digest="1" * 64, purpose_digest="2" * 64,
            recipient_digest="3" * 64, now_ms=20,
        )
    assert not executed


def test_exported_recovery_receipt_substitution_fails_preflight(monkeypatch):
    monkeypatch.setattr(module, "SyntheticClaimRecoveryReview", object)
    with pytest.raises(
        module.SyntheticClaimRecoveryRejected,
        match="result contract changed",
    ):
        module.review_synthetic_claim_write_recovery(
            None, None, None, None, None, None, None,
            step_id="fixture", issuer_digest="0" * 64,
            subject_digest="1" * 64, purpose_digest="2" * 64,
            recipient_digest="3" * 64, now_ms=20,
        )
