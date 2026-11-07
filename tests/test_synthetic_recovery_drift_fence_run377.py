"""A recovery diagnostic must reject observed cross-store mid-read changes."""

import hashlib
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_recovery_triage import (
    SyntheticRecoveryRejected,
    review_synthetic_write_recovery,
)


class NoBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("the recovery diagnostic cannot execute a backend")


def _fixture(tmp_path: Path):
    call = ToolCall("fixture", "mock", "local", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("fixture", "mock", Effect.WRITE, "mock", NoBackend()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("step", call),),
    )
    path = tmp_path / "reservations.sqlite"
    store = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    return journal, path, store, audit, registry, call


def _review(state, **kwargs):
    journal, path, _store, audit, registry, call = state
    return review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="step", **kwargs,
    )


def _reserve(state, label="late"):
    _journal, _path, store, _audit, registry, call = state
    occurrence = "occ_" + hashlib.sha256(label.encode("utf-8")).hexdigest()
    return store.reserve_synthetic(
        registry, call, OneShotAuthorization(label, call.request_id, 100),
        occurrence_id=occurrence, now_ms=11,
    )


def test_stable_three_store_read_returns_no_authority(tmp_path: Path):
    outcome = _review(_fixture(tmp_path))
    assert outcome.step_state == "pending"
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False
    assert outcome.external_outcome_known is False


def test_late_plan_append_is_detected(tmp_path: Path, monkeypatch):
    state = _fixture(tmp_path)
    original = SyntheticPlanJournal.recover
    counts = []

    def inject(self, *, retained=None):
        result = original(self, retained=retained)
        counts.append(True)
        if len(counts) == 1:
            self.append("step", StepState.RUNNING, expected_revision=0, at_ms=10)
        return result

    monkeypatch.setattr(SyntheticPlanJournal, "recover", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="plan changed"):
        _review(state)


def test_late_reservation_is_detected(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_recovery_triage as module

    state = _fixture(tmp_path)
    original = module.review_audit_continuity
    counts = []

    def inject(*args, **kwargs):
        result = original(*args, **kwargs)
        counts.append(True)
        if len(counts) == 1:
            _reserve(state)
        return result

    monkeypatch.setattr(module, "review_audit_continuity", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="reservation history changed"):
        _review(state)


def test_late_audit_append_detected_even_without_sidecar(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_recovery_triage as module

    state = _fixture(tmp_path)
    original = module.review_audit_continuity
    counts = []

    def inject(*args, **kwargs):
        result = original(*args, **kwargs)
        counts.append(True)
        if len(counts) == 1:
            state[3].append(state[5], outcome="fixture_only")
        return result

    monkeypatch.setattr(module, "review_audit_continuity", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="audit history changed"):
        _review(state)


def test_late_sidecar_link_is_detected(tmp_path: Path, monkeypatch):
    import ark.agency.synthetic_recovery_triage as module

    state = _fixture(tmp_path)
    receipt = _reserve(state, "first")
    event = state[3].append(state[5], outcome="synthetic_audit_before_mock")
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links #1 %.sqlite")
    original = module.read_synthetic_ledger_witness
    counts = []

    def inject(*args, **kwargs):
        result = original(*args, **kwargs)
        counts.append(True)
        if len(counts) == 1:
            links.link_synthetic(
                state[4], state[5], state[2], receipt, state[3], event, at_ms=13,
            )
        return result

    monkeypatch.setattr(module, "read_synthetic_ledger_witness", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="link history changed"):
        _review(state, link_store=links)


def test_stable_sidecar_links_remain_diagnostic_only(tmp_path: Path):
    state = _fixture(tmp_path)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    receipt = _reserve(state)
    event = state[3].append(state[5], outcome="synthetic_audit_before_mock")
    links.link_synthetic(
        state[4], state[5], state[2], receipt, state[3], event, at_ms=13,
    )
    outcome = _review(state, link_store=links)
    assert outcome.matching_audit_links == ((receipt.occurrence_id, event.event_id),)
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False
    assert outcome.external_outcome_known is False
