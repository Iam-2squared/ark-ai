"""Read-only claimed-approval provenance must not become execution authority."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_occurrence_link_review import (
    SyntheticClaimOccurrenceLinkStore,
)
from ark.agency.synthetic_claim_recovery_provenance_review import (
    SyntheticClaimProvenanceRejected,
    review_synthetic_claim_write_provenance,
)


class NeverBackend:
    def execute(self, call):
        raise AssertionError("claim provenance cannot execute a backend")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def fixture(tmp_path: Path):
    call = ToolCall("fixture", "write", "sandbox", {"secret": "NEVER-DISCLOSE"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    claim = make_synthetic_approval_claim(
        registry, call, issuer_digest=digest("issuer"),
        subject_digest=digest("subject"), purpose_digest=digest("purpose"),
        recipient_digest=digest("recipient"), nonce_digest=digest("nonce"),
        issued_at_ms=10, expires_at_ms=100,
    )
    cancellation = SyntheticCancellationLedger(tmp_path / "cancel.sqlite")
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "reservations # %.sqlite"
    ledger = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticClaimOccurrenceLinkStore(tmp_path / "claim-link.sqlite")
    receipt = ledger.reserve_synthetic(
        registry, call, OneShotAuthorization("fixture-token", call.request_id, 500),
        occurrence_id="occ_" + digest("first"), now_ms=11,
    )
    links.link_synthetic(
        claim, cancellation, registry, call, ledger, receipt, now_ms=20,
    )
    return claim, cancellation, journal, path, ledger, audit, registry, call, links, receipt


def review(state, **overrides):
    claim, cancellation, journal, path, _, audit, registry, call, links, receipt = state
    kwargs = dict(
        step_id="root", occurrence_id=receipt.occurrence_id,
        issuer_digest=claim.issuer_digest, subject_digest=claim.subject_digest,
        purpose_digest=claim.purpose_digest, recipient_digest=claim.recipient_digest,
        now_ms=21,
    )
    kwargs.update(overrides)
    return review_synthetic_claim_write_provenance(
        claim, cancellation, journal, path, audit, registry, call, links, **kwargs,
    )


def test_saved_pair_is_diagnostic_only(tmp_path: Path):
    state = fixture(tmp_path)
    result = review(state)
    assert result.approval_id == state[0].approval_id
    assert result.occurrence_id == state[9].occurrence_id
    assert result.claim_link_count == 1
    assert result.step_state == "pending"
    assert result.ambiguous_write is False
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "NEVER-DISCLOSE" not in repr(result)


def test_unknown_running_write_stays_unknown(tmp_path: Path):
    state = fixture(tmp_path)
    state[2].append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    result = review(state)
    assert result.step_state == "running"
    assert result.ambiguous_write is True
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("wrong", [True, None, "wrong", "occ_" + digest("other")])
def test_only_exact_claimed_occurrence_is_accepted(tmp_path: Path, wrong):
    state = fixture(tmp_path)
    with pytest.raises(RuntimeError, match="exact|matching"):
        review(state, occurrence_id=wrong)


def test_unlinked_reservation_cannot_be_elevated_to_provenance(tmp_path: Path):
    state = fixture(tmp_path)
    state[4].reserve_synthetic(
        state[6], state[7],
        OneShotAuthorization("second-token", state[7].request_id, 500),
        occurrence_id="occ_" + digest("second"), now_ms=12,
    )
    with pytest.raises(SyntheticClaimProvenanceRejected, match="exactly one"):
        review(state)


@pytest.mark.parametrize("sql", [
    "DELETE FROM synthetic_claim_occurrence_links",
    "UPDATE synthetic_claim_occurrence_links SET linked_at_ms=21",
])
def test_sidecar_rollback_or_tamper_never_passes(tmp_path: Path, sql: str):
    state = fixture(tmp_path)
    with sqlite3.connect(state[8].path) as conn:
        conn.execute(sql)
    with pytest.raises(RuntimeError):
        review(state)


def test_persisted_reservation_tamper_never_passes(tmp_path: Path):
    state = fixture(tmp_path)
    with sqlite3.connect(state[3]) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_reservations SET reserved_at_ms=22"
        )
    with pytest.raises(RuntimeError):
        review(state)


def test_independent_link_witness_rejects_deleted_history(tmp_path: Path):
    state = fixture(tmp_path)
    witness = state[8].read_witness()
    with sqlite3.connect(state[8].path) as conn:
        conn.execute("DELETE FROM synthetic_claim_occurrence_links")
    with pytest.raises(RuntimeError, match="retained"):
        review(state, retained_claim_links=witness)


def test_new_unrelated_cancellation_between_reviews_is_veto(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_claim_recovery_provenance_review as module

    state = fixture(tmp_path)
    original = module.review_synthetic_claim_occurrence_sources
    count = 0

    def inject(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 1:
            state[1].cancel_synthetic(
                "approval_" + digest("another"), at_ms=21,
            )
        return result

    monkeypatch.setattr(module, "review_synthetic_claim_occurrence_sources", inject)
    with pytest.raises(RuntimeError):
        review(state)


def test_sidecar_append_during_recovery_is_rejected(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_claim_recovery_provenance_review as module

    state = fixture(tmp_path)
    original = module.review_synthetic_claim_occurrence_sources
    count = 0

    def inject(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 1:
            claim = make_synthetic_approval_claim(
                state[6], state[7], issuer_digest=digest("issuer"),
                subject_digest=digest("subject"), purpose_digest=digest("purpose"),
                recipient_digest=digest("recipient"), nonce_digest=digest("later"),
                issued_at_ms=10, expires_at_ms=100,
            )
            receipt = state[4].reserve_synthetic(
                state[6], state[7],
                OneShotAuthorization("later-token", state[7].request_id, 500),
                occurrence_id="occ_" + digest("later"), now_ms=12,
            )
            state[8].link_synthetic(
                claim, state[1], state[6], state[7], state[4],
                receipt, now_ms=21,
            )
        return result

    monkeypatch.setattr(module, "review_synthetic_claim_occurrence_sources", inject)
    with pytest.raises(SyntheticClaimProvenanceRejected, match="changed"):
        review(state)


@pytest.mark.parametrize("which", ["reservation", "sidecar"])
def test_missing_initialized_store_not_recreated(tmp_path: Path, which: str):
    state = fixture(tmp_path)
    path = state[3] if which == "reservation" else state[8].path
    path.rename(tmp_path / ("moved-" + which + ".sqlite"))
    with pytest.raises(RuntimeError):
        review(state)
    assert not path.exists()


def test_bad_retained_claim_link_witness_denied(tmp_path: Path):
    state = fixture(tmp_path)
    with pytest.raises(RuntimeError, match="retained"):
        review(state, retained_claim_links=object())
