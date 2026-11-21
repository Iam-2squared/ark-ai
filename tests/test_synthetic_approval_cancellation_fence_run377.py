"""Deny-only durable cancellation fence regression fixtures (no ToolBackend call)."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_fence_review import (
    SyntheticApprovalFenceRejected,
    review_synthetic_approval_cancellation_fence,
)
from ark.agency.synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationRejected,
)
from ark.agency.synthetic_approval_claim_review import (
    SyntheticApprovalRejected,
    make_synthetic_approval_claim,
)


class MustNotExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a disconnected review must never execute a tool")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path):
    call = ToolCall("writer", "write", "sandbox", {"payload": "private-fixture"})
    registry = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "offline", MustNotExecute()),
    ))
    claim = make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_digest("issuer"),
        subject_digest=_digest("subject"),
        purpose_digest=_digest("purpose"),
        recipient_digest=_digest("recipient"),
        nonce_digest=_digest("nonce"),
        issued_at_ms=10,
        expires_at_ms=100,
    )
    path = tmp_path / "revocation #1 %.sqlite"
    return registry, call, claim, SyntheticCancellationLedger(path), path


def _review(fixture, **changes):
    registry, call, claim, ledger, _path = fixture
    kwargs = {
        "issuer_digest": claim.issuer_digest,
        "subject_digest": claim.subject_digest,
        "purpose_digest": claim.purpose_digest,
        "recipient_digest": claim.recipient_digest,
        "now_ms": 20,
    }
    kwargs.update(changes)
    return review_synthetic_approval_cancellation_fence(
        claim, registry, call, ledger, **kwargs,
    )


def test_absent_cancellation_is_not_consent_or_permission(tmp_path: Path):
    fixture = _fixture(tmp_path)
    claim = fixture[2]
    result = _review(fixture)
    assert result.approval_id == claim.approval_id
    assert result.bound_action_id == claim.bound_action_id
    assert result.cancellation_event_count == 0
    assert result.cancellation_tail_hash.startswith("cancel_")
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert "private-fixture" not in repr(result)


def test_persistent_cancelled_claim_is_denied_across_restart(tmp_path: Path):
    registry, call, claim, ledger, path = _fixture(tmp_path)
    witness = ledger.cancel_synthetic(claim.approval_id, at_ms=15)
    reopened = SyntheticCancellationLedger(path)
    with pytest.raises(SyntheticApprovalFenceRejected, match="cancelled"):
        review_synthetic_approval_cancellation_fence(
            claim, registry, call, reopened,
            issuer_digest=claim.issuer_digest,
            subject_digest=claim.subject_digest,
            purpose_digest=claim.purpose_digest,
            recipient_digest=claim.recipient_digest,
            now_ms=20, retained=witness,
        )


def test_unrelated_prior_cancellation_preserves_local_diagnostic(tmp_path: Path):
    fixture = _fixture(tmp_path)
    ledger = fixture[3]
    earlier = ledger.cancel_synthetic("approval_" + _digest("other"), at_ms=11)
    receipt = _review(fixture, retained=earlier)
    assert receipt.cancellation_event_count == 1
    assert receipt.cancellation_tail_hash == earlier.tail_hash
    assert receipt.dispatch_authorized is False


@pytest.mark.parametrize("target", ["target", "unrelated"])
def test_append_between_veto_reads_is_denied(tmp_path: Path, monkeypatch, target):
    fixture = _fixture(tmp_path)
    claim, ledger = fixture[2:4]
    original = SyntheticCancellationLedger.review_state
    calls = []

    def injected(self, approval_id, *, retained=None):
        state = original(self, approval_id, retained=retained)
        calls.append(approval_id)
        if len(calls) == 1:
            cancellation = claim.approval_id if target == "target" else (
                "approval_" + _digest("other")
            )
            self.cancel_synthetic(cancellation, at_ms=20)
        return state

    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", injected)
    with pytest.raises(SyntheticApprovalFenceRejected, match="changed"):
        _review(fixture)
    assert len(calls) == 2
    assert ledger.read_witness().event_count == 1


def test_retained_history_roll_back_is_denied(tmp_path: Path):
    fixture = _fixture(tmp_path)
    ledger, path = fixture[3:]
    retained = ledger.cancel_synthetic("approval_" + _digest("other"), at_ms=11)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_claim_cancellations")
    with pytest.raises(SyntheticCancellationRejected, match="retained"):
        _review(fixture, retained=retained)


def test_future_cancellation_clock_is_fail_closed(tmp_path: Path):
    fixture = _fixture(tmp_path)
    fixture[3].cancel_synthetic("approval_" + _digest("other"), at_ms=30)
    with pytest.raises(SyntheticApprovalFenceRejected, match="clock"):
        _review(fixture, now_ms=20)


@pytest.mark.parametrize("now_ms", [True, -1, 2**63, "20"])
def test_exact_bounded_clock_input(tmp_path: Path, now_ms):
    with pytest.raises(SyntheticApprovalFenceRejected, match="exact"):
        _review(_fixture(tmp_path), now_ms=now_ms)


def test_claim_expiry_and_actor_mismatch_still_fail(tmp_path: Path):
    fixture = _fixture(tmp_path)
    with pytest.raises(SyntheticApprovalRejected, match="current"):
        _review(fixture, now_ms=100)
    with pytest.raises(SyntheticApprovalRejected, match="differs"):
        _review(fixture, purpose_digest=_digest("forged-purpose"))


def test_reflective_claim_change_during_review_is_denied(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_approval_cancellation_fence_review as module

    fixture = _fixture(tmp_path)
    original = module.review_synthetic_approval_claim

    def mutate_after_review(envelope, *args, **kwargs):
        result = original(envelope, *args, **kwargs)
        object.__setattr__(envelope, "nonce_digest", _digest("late-mutation"))
        return result

    monkeypatch.setattr(module, "review_synthetic_approval_claim", mutate_after_review)
    with pytest.raises(SyntheticApprovalFenceRejected, match="changed"):
        _review(fixture)


def test_stale_ledger_file_is_not_silently_recreated(tmp_path: Path):
    fixture = _fixture(tmp_path)
    _registry, _call, _claim, _ledger, path = fixture
    path.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        _review(fixture)
    assert not path.exists()


def test_invalid_retained_witness_is_denied(tmp_path: Path):
    fixture = _fixture(tmp_path)
    with pytest.raises(SyntheticApprovalFenceRejected, match="exact"):
        _review(fixture, retained=object())


def test_different_registry_binding_does_not_pass_fence(tmp_path: Path):
    registry, call, claim, ledger, _ = _fixture(tmp_path)
    other = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "changed", MustNotExecute()),
    ))
    assert other.revision != registry.revision
    with pytest.raises(SyntheticApprovalRejected, match="binding differs"):
        review_synthetic_approval_cancellation_fence(
            claim, other, call, ledger,
            issuer_digest=claim.issuer_digest,
            subject_digest=claim.subject_digest,
            purpose_digest=claim.purpose_digest,
            recipient_digest=claim.recipient_digest,
            now_ms=20,
        )
