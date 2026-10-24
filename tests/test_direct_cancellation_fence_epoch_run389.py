"""Direct synthetic cancellation fences must pin inputs before first SQLite read."""

import hashlib
from pathlib import Path
from types import MappingProxyType

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_fence_review import (
    SyntheticApprovalFenceRejected,
    review_synthetic_approval_cancellation_fence,
)
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic approval never dispatches")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _fixture(tmp_path: Path):
    call = ToolCall("offline", "mock", "local", {"private": "fixture"})
    registry = ToolRegistry((
        ToolRegistration("offline", "mock", Effect.WRITE, "inert", NeverExecute()),
    ))
    claim = make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_digest("issuer"), subject_digest=_digest("subject"),
        purpose_digest=_digest("purpose"), recipient_digest=_digest("recipient"),
        nonce_digest=_digest("nonce"), issued_at_ms=10, expires_at_ms=100,
    )
    ledger = SyntheticCancellationLedger(tmp_path / "cancellation.sqlite")
    return call, registry, claim, ledger


def _review(state, *, retained=None):
    call, registry, claim, ledger = state
    return review_synthetic_approval_cancellation_fence(
        claim, registry, call, ledger,
        issuer_digest=claim.issuer_digest, subject_digest=claim.subject_digest,
        purpose_digest=claim.purpose_digest, recipient_digest=claim.recipient_digest,
        now_ms=20, retained=retained,
    )


def test_stable_direct_fence_never_proves_consent(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state, retained=state[3].read_witness())
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("which", ["source", "arguments", "scope"])
def test_first_cancellation_read_cannot_change_original_inputs(
    tmp_path: Path, monkeypatch, which: str,
):
    state = _fixture(tmp_path)
    original = SyntheticCancellationLedger.review_state
    calls = 0

    def injected(self, approval_id, *, retained=None):
        nonlocal calls
        result = original(self, approval_id, retained=retained)
        calls += 1
        if calls == 1:
            if which == "source":
                self.path = Path(str(self.path))
            elif which == "arguments":
                object.__setattr__(
                    state[0], "arguments", MappingProxyType(dict(state[0].arguments)),
                )
            else:
                object.__setattr__(state[0], "scope", "other-local-scope")
        return result

    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", injected)
    with pytest.raises(SyntheticApprovalFenceRejected, match="input|source"):
        _review(state)


def test_retained_history_swapped_to_other_valid_witness_is_rejected(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    ledger = state[3]
    retained = ledger.read_witness()
    ledger.cancel_synthetic("approval_" + _digest("unrelated"), at_ms=11)
    later = ledger.read_witness()
    original = SyntheticCancellationLedger.review_state

    def injected(self, approval_id, *, retained=None):
        result = original(self, approval_id, retained=retained)
        if retained is not None and retained is history:
            object.__setattr__(history, "event_count", later.event_count)
            object.__setattr__(history, "tail_hash", later.tail_hash)
            object.__setattr__(history, "last_cancelled_at_ms", later.last_cancelled_at_ms)
        return result

    history = retained
    monkeypatch.setattr(SyntheticCancellationLedger, "review_state", injected)
    with pytest.raises(SyntheticApprovalFenceRejected, match="retained history"):
        _review(state, retained=history)
