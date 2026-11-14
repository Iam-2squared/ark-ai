"""Cross-store provenance must reject a transient reflected input epoch.

Fixture only: no external ToolBackend, consent validation or write replay.
"""

import hashlib
from pathlib import Path
from types import MappingProxyType

import pytest

import ark.agency.synthetic_claim_recovery_provenance_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_occurrence_link_review import SyntheticClaimOccurrenceLinkStore


class NeverBackend:
    def execute(self, call):
        raise AssertionError("offline synthetic provenance never dispatches")


def _hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _fixture(tmp_path: Path):
    call = ToolCall("fixture", "write", "local", {"secret": "PRIVATE-FIXTURE"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    claim = make_synthetic_approval_claim(
        registry, call, issuer_digest=_hash("issuer"),
        subject_digest=_hash("subject"), purpose_digest=_hash("purpose"),
        recipient_digest=_hash("recipient"), nonce_digest=_hash("nonce"),
        issued_at_ms=10, expires_at_ms=100,
    )
    cancellation = SyntheticCancellationLedger(tmp_path / "cancel.sqlite")
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (PlanStep("root", call),))
    path = tmp_path / "reservations.sqlite"
    reservations = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    links = SyntheticClaimOccurrenceLinkStore(tmp_path / "claim-links.sqlite")
    receipt = reservations.reserve_synthetic(
        registry, call, OneShotAuthorization("fixture-token", call.request_id, 500),
        occurrence_id="occ_" + _hash("reservation"), now_ms=11,
    )
    links.link_synthetic(claim, cancellation, registry, call, reservations, receipt, now_ms=20)
    return claim, cancellation, journal, path, audit, registry, call, links, receipt


def _review(state, **kwargs):
    claim, cancellation, journal, path, audit, registry, call, links, receipt = state
    arguments = dict(
        step_id="root", occurrence_id=receipt.occurrence_id,
        issuer_digest=claim.issuer_digest, subject_digest=claim.subject_digest,
        purpose_digest=claim.purpose_digest, recipient_digest=claim.recipient_digest,
        now_ms=21,
    )
    arguments.update(kwargs)
    return module.review_synthetic_claim_write_provenance(
        claim, cancellation, journal, path, audit, registry, call, links, **arguments,
    )


def test_stable_cross_store_provenance_is_diagnostic_only(tmp_path: Path):
    result = _review(_fixture(tmp_path))
    assert result.claim_link_count == 1
    assert result.dispatch_authorized is False
    assert result.human_consent_verified is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "PRIVATE-FIXTURE" not in repr(result)


@pytest.mark.parametrize("which", ["source", "topology", "call"])
def test_transient_swap_after_first_recovery_denied_before_next_pass(
    tmp_path: Path, monkeypatch, which: str,
):
    state = _fixture(tmp_path)
    original_recovery = module.review_synthetic_claim_write_recovery
    original_sources = module.review_synthetic_claim_occurrence_sources
    original_path = state[7].path
    original_steps = state[2]._steps
    original_arguments = state[6].arguments
    recovery_calls = 0
    next_calls = 0

    def inject_recovery(*args, **kwargs):
        nonlocal recovery_calls
        result = original_recovery(*args, **kwargs)
        recovery_calls += 1
        if recovery_calls == 1:
            if which == "source":
                state[7].path = Path(str(state[7].path))
            elif which == "topology":
                state[2]._steps = tuple(list(state[2]._steps))
            else:
                object.__setattr__(
                    state[6], "arguments", MappingProxyType(dict(state[6].arguments)),
                )
        return result

    def next_pass(*args, **kwargs):
        nonlocal next_calls
        next_calls += 1
        # The earlier final-only guard misses a transient reflected replacement
        # when a second callback restores the original carrier before return.
        if which == "source":
            state[7].path = original_path
        elif which == "topology":
            state[2]._steps = original_steps
        else:
            object.__setattr__(state[6], "arguments", original_arguments)
        return original_sources(*args, **kwargs)

    monkeypatch.setattr(module, "review_synthetic_claim_write_recovery", inject_recovery)
    monkeypatch.setattr(module, "review_synthetic_claim_occurrence_sources", next_pass)
    with pytest.raises(module.SyntheticClaimProvenanceRejected, match="changed"):
        _review(state)
    assert recovery_calls == 1
    assert next_calls == 0


def test_claim_reflection_after_first_source_read_denied_without_second_recovery(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    original = module.review_synthetic_claim_occurrence_sources
    phases = 0

    def mutate(*args, **kwargs):
        nonlocal phases
        result = original(*args, **kwargs)
        phases += 1
        if phases == 1:
            object.__setattr__(state[0], "issuer_digest", _hash("another-issuer"))
        return result

    monkeypatch.setattr(module, "review_synthetic_claim_occurrence_sources", mutate)
    with pytest.raises(module.SyntheticClaimProvenanceRejected, match="changed"):
        _review(state)
    assert phases == 1


def test_retained_link_witness_mutation_denied_between_read_phases(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    witness = state[7].read_witness()
    original = module.review_synthetic_claim_write_recovery

    def mutate(*args, **kwargs):
        receipt = original(*args, **kwargs)
        object.__setattr__(witness, "tail_hash", "0" * 64)
        return receipt

    monkeypatch.setattr(module, "review_synthetic_claim_write_recovery", mutate)
    with pytest.raises(module.SyntheticClaimProvenanceRejected, match="witness|changed"):
        _review(state, retained_claim_links=witness)
