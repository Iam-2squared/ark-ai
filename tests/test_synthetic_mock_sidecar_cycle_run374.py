"""A synthetic mock cycle may link audit and reservation but must never dispatch."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


class NoBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("optional sidecar must not activate a backend")


def _setup(tmp_path: Path, *, audit_clock=12):
    call = ToolCall("mock", "write", "local", {"offline": True})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "reservations.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: audit_clock)
    registry = ToolRegistry((
        ToolRegistration("mock", "write", Effect.WRITE, "inert", NoBackend()),
    ))
    path = tmp_path / "audit-links.sqlite"
    links = SyntheticOccurrenceAuditLinkStore(path)
    token = OneShotAuthorization("token-one", call.request_id, 1000)
    return journal, ledger, audit, registry, call, links, token, path


def _run(state, *, occurrence="first", fault_at=None, link="present"):
    journal, ledger, audit, registry, call, links, token, _path = state
    occ = "occ_" + hashlib.sha256(occurrence.encode("utf-8")).hexdigest()
    if link == "present":
        link_store = links
    else:
        link_store = link
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root", occurrence_id=occ, now_ms=10,
        fault_at=fault_at, link_store=link_store,
    )


def test_success_records_link_but_never_an_external_outcome(tmp_path: Path):
    state = _setup(tmp_path)
    receipt = _run(state)
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    link = state[5].read_witness()
    assert link.event_count == 1
    assert receipt.audit_event_id == 1
    assert link.last_link_at_ms == 12
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False


def test_after_audit_link_fault_leaves_unknown_and_cannot_retry(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected, match="audit link"):
        _run(state, fault_at="after_audit_link")
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[5].read_witness().event_count == 1
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(state, occurrence="different")
    assert state[5].read_witness().event_count == 1


@pytest.mark.parametrize("fault", [
    "after_running", "after_reservation", "after_pre_action_audit",
])
def test_earlier_faults_never_create_a_link(tmp_path: Path, fault: str):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected):
        _run(state, fault_at=fault)
    assert state[5].read_witness().event_count == 0
    assert state[0].recover().ambiguous_running_steps == ("root",)


def test_audit_link_fault_without_sidecar_is_preflight_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCycleRejected, match="requires a synthetic sidecar"):
        _run(state, fault_at="after_audit_link", link=None)
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []


@pytest.mark.parametrize("wrong", [False, 42, "sidecar", object()])
def test_invalid_sidecar_type_is_rejected_before_write(tmp_path: Path, wrong):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCycleRejected, match="exact synthetic mock"):
        _run(state, link=wrong)
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[5].read_witness().event_count == 0


def test_missing_sidecar_file_leaves_unknown_not_new_ledger(tmp_path: Path):
    state = _setup(tmp_path)
    state[-1].unlink()
    with pytest.raises(sqlite3.OperationalError):
        _run(state)
    assert not state[-1].exists()
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1


def test_schema_drift_causes_unknown_write_not_mock_success(tmp_path: Path):
    state = _setup(tmp_path)
    with sqlite3.connect(state[-1]) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(SyntheticAuditLinkRejected, match="schema version"):
        _run(state)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1


def test_uncertain_local_clock_after_reservation_remains_unknown(tmp_path: Path):
    state = _setup(tmp_path, audit_clock=5)
    with pytest.raises(SyntheticAuditLinkRejected, match="pre-action audit"):
        _run(state)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[5].read_witness().event_count == 0
    assert state[1].count_synthetic() == 1
