"""Cross-store crash diagnosis remains disconnected and denies all WRITE replay."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import (
    ActionAuditSchemaError,
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_continuity_review import (
    read_synthetic_ledger_witness,
)
from ark.agency.synthetic_recovery_triage import (
    SyntheticRecoveryRejected,
    review_synthetic_write_recovery,
)


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("recovery fixture must never execute a backend")


def _registry(effect=Effect.WRITE, backend_id="fixture") -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration("offline", "mock", effect, backend_id, NeverExecute()),
    ))


def _setup(tmp_path: Path):
    call = ToolCall("offline", "mock", "local", {"v": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "reservations.sqlite"
    store = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = _registry()
    return journal, path, store, audit, registry, call


def _reserve(store, registry, call, name="one"):
    occurrence = "occ_" + hashlib.sha256(name.encode("utf-8")).hexdigest()
    return store.reserve_synthetic(
        registry, call, OneShotAuthorization(name, call.request_id, 1000),
        occurrence_id=occurrence, now_ms=11,
    )


def _review(state):
    journal, path, _store, audit, registry, call = state
    return review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="root",
    )


def test_pending_empty_recovery_remains_inert(tmp_path: Path):
    result = _review(_setup(tmp_path))
    assert result.step_state == "pending"
    assert result.ambiguous_write is False
    assert result.matching_occurrences == ()
    assert result.audit_witness.event_count == 0
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False


def test_running_with_matching_reservation_and_audit_is_still_unknown(tmp_path: Path):
    state = _setup(tmp_path)
    journal, _path, store, audit, registry, call = state
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    receipt = _reserve(store, registry, call)
    audit.append(call, outcome="synthetic_fixture_only")
    result = _review(state)
    assert result.ambiguous_write is True
    assert result.step_state == "running"
    assert result.matching_occurrences == (receipt.occurrence_id,)
    assert result.audit_witness.event_count == 1
    assert result.request_id == receipt.request_id
    assert result.bound_action_id == receipt.bound_action_id
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False


def test_succeeded_plan_does_not_certify_external_effect(tmp_path: Path):
    state = _setup(tmp_path)
    journal = state[0]
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    journal.append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=12)
    result = _review(state)
    assert result.step_state == "succeeded"
    assert result.ambiguous_write is False
    assert result.external_outcome_known is False


def test_retained_plan_ledger_and_audit_accept_untampered_history(tmp_path: Path):
    state = _setup(tmp_path)
    journal, path, store, audit, registry, call = state
    plan = journal.recover().tail
    ledger = read_synthetic_ledger_witness(path)
    aud = review_audit_continuity(audit)
    _reserve(store, registry, call)
    outcome = review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="root",
        retained_plan=plan, retained_ledger=ledger, retained_audit=aud,
    )
    assert len(outcome.matching_occurrences) == 1
    assert outcome.dispatch_authorized is False


def test_conflicting_stored_registry_identity_is_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    _reserve(state[2], state[4], state[5])
    with pytest.raises(SyntheticRecoveryRejected, match="conflicting registry"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], _registry(backend_id="other"),
            state[5], step_id="root",
        )


def test_matching_request_with_rewritten_bound_identity_is_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    _reserve(state[2], state[4], state[5])
    with sqlite3.connect(state[1]) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_reservations SET bound_action_id=?",
            ("bound_" + "f" * 64,),
        )
    with pytest.raises(SyntheticRecoveryRejected, match="conflicting registry"):
        _review(state)


def test_retained_ledger_detects_deletion_without_replacement(tmp_path: Path):
    state = _setup(tmp_path)
    _reserve(state[2], state[4], state[5])
    retained = read_synthetic_ledger_witness(state[1])
    with sqlite3.connect(state[1]) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    with pytest.raises(Exception, match="retained reservation history changed"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], state[4], state[5],
            step_id="root", retained_ledger=retained,
        )


def test_retained_audit_detects_modified_historical_event(tmp_path: Path):
    state = _setup(tmp_path)
    state[3].append(state[5], outcome="original")
    retained = review_audit_continuity(state[3])
    with sqlite3.connect(state[3].path) as conn:
        conn.execute("UPDATE action_events SET outcome='changed' WHERE event_id=1")
    with pytest.raises(ActionAuditSchemaError, match="prefix differs"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], state[4], state[5],
            step_id="root", retained_audit=retained,
        )


def test_missing_ledger_fails_and_is_never_recreated(tmp_path: Path):
    state = _setup(tmp_path)
    state[1].unlink()
    with pytest.raises(SyntheticRecoveryRejected, match="incomplete"):
        _review(state)
    assert not state[1].exists()


def test_missing_audit_fails_and_is_never_recreated(tmp_path: Path):
    state = _setup(tmp_path)
    state[3].path.unlink()
    with pytest.raises(ActionAuditSchemaError, match="cannot read audit"):
        _review(state)
    assert not state[3].path.exists()


def test_step_request_mismatch_is_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    different = ToolCall("offline", "mock", "local", {"v": 2})
    with pytest.raises(SyntheticRecoveryRejected, match="plan step action"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], state[4], different, step_id="root",
        )


def test_read_only_tool_and_unknown_step_are_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRecoveryRejected, match="only WRITE"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], _registry(Effect.READ),
            state[5], step_id="root",
        )
    with pytest.raises(SyntheticRecoveryRejected, match="not in"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], state[4], state[5], step_id="absent",
        )


@pytest.mark.parametrize("bad", [None, "missing", 12, False])
def test_path_requires_pathlib_instance(tmp_path: Path, bad):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRecoveryRejected, match="exact fixture"):
        review_synthetic_write_recovery(
            state[0], bad, state[3], state[4], state[5], step_id="root",
        )


def test_special_characters_in_ledger_filename_are_safe(tmp_path: Path):
    state = _setup(tmp_path / "dir #100")
    result = _review(state)
    assert result.matching_occurrences == ()
