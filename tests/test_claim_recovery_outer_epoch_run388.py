"""Direct claim/recovery review must bind the whole source and action epoch.

Synthetic fixtures only: no human consent, backend or automatic WRITE replay.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_claim_recovery_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_recovery_review import SyntheticClaimRecoveryRejected


class NeverBackend:
    def execute(self, call):
        raise AssertionError("disconnected review must never dispatch")


def _hash(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _fixture(tmp_path: Path):
    call = ToolCall("fixture", "write", "sandbox", {"private": "DO-NOT-DISCLOSE"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    claim = make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_hash("issuer"), subject_digest=_hash("subject"),
        purpose_digest=_hash("purpose"), recipient_digest=_hash("recipient"),
        nonce_digest=_hash("nonce"), issued_at_ms=10, expires_at_ms=100,
    )
    cancellation = SyntheticCancellationLedger(tmp_path / "veto.sqlite")
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    occurrence_path = tmp_path / "occurrence.sqlite"
    SyntheticOccurrenceStore(occurrence_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    return claim, cancellation, journal, occurrence_path, audit, registry, call


def _review(state):
    claim, veto, journal, occurrence, audit, registry, call = state
    return module.review_synthetic_claim_write_recovery(
        claim, veto, journal, occurrence, audit, registry, call,
        step_id="root", issuer_digest=claim.issuer_digest,
        subject_digest=claim.subject_digest, purpose_digest=claim.purpose_digest,
        recipient_digest=claim.recipient_digest, now_ms=20,
    )


@pytest.mark.parametrize("source_index", [1, 2, 4])
@pytest.mark.parametrize("phase", ["veto", "recovery"])
def test_equal_path_replacement_between_reviews_is_denied(
    tmp_path: Path, monkeypatch, source_index: int, phase: str,
):
    state = _fixture(tmp_path)
    attr = "_path" if source_index == 2 else "path"
    target = state[source_index]
    hook = (
        "review_synthetic_approval_cancellation_fence"
        if phase == "veto" else "review_synthetic_write_recovery"
    )
    original = getattr(module, hook)
    calls = 0

    def retarget(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            previous = getattr(target, attr)
            setattr(target, attr, Path(str(previous)))
        return result

    monkeypatch.setattr(module, hook, retarget)
    with pytest.raises(SyntheticClaimRecoveryRejected, match="source"):
        _review(state)
    assert calls == 1


@pytest.mark.parametrize("phase", ["veto", "recovery"])
def test_original_toolcall_cannot_be_swapped_during_review(
    tmp_path: Path, monkeypatch, phase: str,
):
    state = _fixture(tmp_path)
    hook = (
        "review_synthetic_approval_cancellation_fence"
        if phase == "veto" else "review_synthetic_write_recovery"
    )
    original = getattr(module, hook)

    def mutate_call(*args, **kwargs):
        receipt = original(*args, **kwargs)
        object.__setattr__(state[6], "scope", "swapped-after-callback")
        return receipt

    monkeypatch.setattr(module, hook, mutate_call)
    with pytest.raises(SyntheticClaimRecoveryRejected, match="action"):
        _review(state)


def test_stable_pending_recovery_has_no_execution_authority(tmp_path: Path):
    receipt = _review(_fixture(tmp_path))
    assert receipt.step_state == "pending"
    assert receipt.human_consent_verified is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert "DO-NOT-DISCLOSE" not in repr(receipt)
