"""Deny-only approval/recovery correlation across independent synthetic ledgers."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_fence_review import (
    SyntheticApprovalFenceRejected,
)
from ark.agency.synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationRejected,
)
from ark.agency.synthetic_approval_claim_review import (
    SyntheticApprovalRejected,
    make_synthetic_approval_claim,
)
from ark.agency.synthetic_claim_recovery_review import (
    SyntheticClaimRecoveryRejected,
    review_synthetic_claim_write_recovery,
)
from ark.agency.synthetic_occurrence_audit_link_review import SyntheticOccurrenceAuditLinkStore
from ark.agency.synthetic_recovery_triage import SyntheticRecoveryRejected


class NeverBackend:
    def execute(self, call):
        raise AssertionError("a local diagnosis cannot dispatch a backend")


def _digest(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path):
    call = ToolCall("fixture", "write", "sandbox", {"secret": "PRIVATE-DO-NOT-EMIT"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    envelope = make_synthetic_approval_claim(
        registry, call, issuer_digest=_digest("issuer"),
        subject_digest=_digest("subject"), purpose_digest=_digest("purpose"),
        recipient_digest=_digest("recipient"), nonce_digest=_digest("nonce"),
        issued_at_ms=10, expires_at_ms=100,
    )
    cancellation = SyntheticCancellationLedger(tmp_path / "cancel #1 %.sqlite")
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (PlanStep("root", call),))
    occurrence_path = tmp_path / "occurrence.sqlite"
    store = SyntheticOccurrenceStore(occurrence_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    sidecar = SyntheticOccurrenceAuditLinkStore(tmp_path / "sidecar.sqlite")
    return envelope, cancellation, journal, occurrence_path, store, audit, registry, call, sidecar


def _review(state, **changes):
    envelope, cancellation, journal, path, _store, audit, registry, call, _link = state
    values = {
        "step_id": "root",
        "issuer_digest": envelope.issuer_digest,
        "subject_digest": envelope.subject_digest,
        "purpose_digest": envelope.purpose_digest,
        "recipient_digest": envelope.recipient_digest,
        "now_ms": 20,
    }
    values.update(changes)
    return review_synthetic_claim_write_recovery(
        envelope, cancellation, journal, path, audit, registry, call, **values,
    )


def _reserve(state):
    call, registry, store = state[7], state[6], state[4]
    return store.reserve_synthetic(
        registry, call, OneShotAuthorization("synthetic", call.request_id, 1000),
        occurrence_id="occ_" + _digest("unique"), now_ms=11,
    )


def test_pending_cross_store_review_is_not_permission(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert result.approval_id == state[0].approval_id
    assert result.registry_revision == state[6].revision
    assert result.request_id == state[7].request_id
    assert result.step_state == "pending"
    assert result.ambiguous_write is False
    assert result.matching_occurrences == ()
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "PRIVATE-DO-NOT-EMIT" not in repr(result)


def test_unknown_running_write_remains_nonretryable(tmp_path: Path):
    state = _fixture(tmp_path)
    state[2].append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    reserved = _reserve(state)
    state[5].append(state[7], outcome="synthetic_fixture_only")
    result = _review(state)
    assert result.step_state == "running"
    assert result.ambiguous_write is True
    assert result.matching_occurrences == (reserved.occurrence_id,)
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False


def test_optional_fourth_ledger_does_not_grant_execution(tmp_path: Path):
    state = _fixture(tmp_path)
    reserved = _reserve(state)
    event = state[5].append(state[7], outcome="synthetic_audit_before_mock")
    state[8].link_synthetic(
        state[6], state[7], state[4], reserved, state[5], event, at_ms=13,
    )
    result = _review(state, link_store=state[8])
    assert result.matching_occurrences == (reserved.occurrence_id,)
    assert result.dispatch_authorized is False


def test_prior_unrelated_cancellation_is_retained_without_consent(tmp_path: Path):
    state = _fixture(tmp_path)
    witness = state[1].cancel_synthetic("approval_" + _digest("unrelated"), at_ms=11)
    result = _review(state, retained_cancellation=witness)
    assert result.cancellation_event_count == 1
    assert result.cancellation_tail_hash == witness.tail_hash
    assert result.human_consent_verified is False


def test_claim_already_cancelled_is_denied(tmp_path: Path):
    state = _fixture(tmp_path)
    state[1].cancel_synthetic(state[0].approval_id, at_ms=15)
    with pytest.raises(SyntheticApprovalFenceRejected, match="cancelled"):
        _review(state)


def test_unrelated_cancellation_during_recovery_invalidates_review(
    tmp_path: Path, monkeypatch,
):
    import ark.agency.synthetic_claim_recovery_review as module

    state = _fixture(tmp_path)
    original = module.review_synthetic_write_recovery

    def append_after_recovery(*args, **kwargs):
        result = original(*args, **kwargs)
        state[1].cancel_synthetic("approval_" + _digest("unrelated"), at_ms=20)
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", append_after_recovery)
    with pytest.raises(SyntheticClaimRecoveryRejected, match="changed"):
        _review(state)


def test_retained_cancellation_history_rollback_is_denied(tmp_path: Path):
    state = _fixture(tmp_path)
    retained = state[1].cancel_synthetic("approval_" + _digest("old"), at_ms=11)
    with sqlite3.connect(state[1].path) as conn:
        conn.execute("DELETE FROM synthetic_claim_cancellations")
    with pytest.raises(SyntheticCancellationRejected, match="retained"):
        _review(state, retained_cancellation=retained)


@pytest.mark.parametrize(
    "field", ["issuer_digest", "subject_digest", "purpose_digest", "recipient_digest"],
)
def test_actor_purpose_recipient_mismatch_stays_denied(tmp_path: Path, field: str):
    state = _fixture(tmp_path)
    with pytest.raises(SyntheticApprovalRejected, match="differs"):
        _review(state, **{field: _digest("forged")})


@pytest.mark.parametrize("clock", [-1, True, 9, 100, 2**63])
def test_bad_or_expired_clock_is_denied(tmp_path: Path, clock):
    state = _fixture(tmp_path)
    with pytest.raises((SyntheticApprovalRejected, SyntheticApprovalFenceRejected)):
        _review(state, now_ms=clock)


def test_plan_request_mismatch_is_denied(tmp_path: Path):
    state = list(_fixture(tmp_path))
    different = ToolCall("fixture", "write", "sandbox", {"secret": "different"})
    state[2] = SyntheticPlanJournal(
        tmp_path / "other-plan.sqlite", (PlanStep("root", different),),
    )
    with pytest.raises(SyntheticRecoveryRejected, match="plan step"):
        _review(state)


def test_missing_occurrence_store_is_not_recreated(tmp_path: Path):
    state = _fixture(tmp_path)
    original = state[3]
    original.rename(tmp_path / "moved.sqlite")
    with pytest.raises(SyntheticRecoveryRejected, match="incomplete"):
        _review(state)
    assert not original.exists()


def test_mutated_claim_during_recovery_is_denied(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_claim_recovery_review as module

    state = _fixture(tmp_path)
    original = module.review_synthetic_write_recovery

    def mutate_after_recovery(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(state[0], "nonce_digest", _digest("late"))
        return result

    monkeypatch.setattr(module, "review_synthetic_write_recovery", mutate_after_recovery)
    with pytest.raises(SyntheticApprovalRejected, match="modified"):
        _review(state)


def test_different_registry_revision_is_denied(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[6] = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "changed", NeverBackend()),
    ))
    with pytest.raises(SyntheticApprovalRejected, match="binding"):
        _review(state)
