"""Crash-boundary recovery across actual SQLite reopen, with no ToolBackend."""

import hashlib
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
    SyntheticOccurrenceAuditLinkStore,
)


class MustNeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("backend cannot run in a restart fixture")


def _fixture(root: Path):
    call = ToolCall("offline", "write", "local", {"private": "not-for-backend"})
    steps = (PlanStep("root", call),)
    registry = ToolRegistry((
        ToolRegistration("offline", "write", Effect.WRITE, "synthetic", MustNeverExecute()),
    ))
    journal = SyntheticPlanJournal(root / "plan # %.sqlite", steps)
    ledger = SyntheticOccurrenceStore(root / "reserve # %.sqlite")
    audit = SQLiteActionAudit(root / "audit # %.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(root / "links # %.sqlite")
    return call, registry, steps, journal, ledger, audit, links


def _cycle(items, *, token_id="first", occurrence="first", fault=None):
    call, registry, _steps, journal, ledger, audit, links = items
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call,
        OneShotAuthorization(token_id, call.request_id, 1000),
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(occurrence.encode()).hexdigest(),
        now_ms=10, fault_at=fault, link_store=links,
    )


def _restart(root: Path, items):
    call, registry, steps, *_rest = items
    journal = SyntheticPlanJournal(root / "plan # %.sqlite", steps)
    ledger = SyntheticOccurrenceStore(root / "reserve # %.sqlite")
    audit = SQLiteActionAudit(root / "audit # %.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(root / "links # %.sqlite")
    return call, registry, steps, journal, ledger, audit, links


@pytest.mark.parametrize(("fault", "reserved", "audited", "linked"), [
    ("after_running", 0, 0, 0),
    ("after_reservation", 1, 0, 0),
    ("after_pre_action_audit", 1, 1, 0),
    ("after_audit_link", 1, 1, 1),
    ("after_mock_marker", 1, 1, 1),
])
def test_persisted_unknown_write_is_not_replayed_after_reopen(
    tmp_path: Path, fault: str, reserved: int, audited: int, linked: int,
):
    items = _fixture(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected):
        _cycle(items, fault=fault)
    restarted = _restart(tmp_path, items)
    assert restarted[3].recover().ambiguous_running_steps == ("root",)
    assert restarted[4].count_synthetic() == reserved
    assert len(restarted[5].events()) == audited
    assert restarted[6].read_witness().event_count == linked
    for token_id, occurrence in (
        ("first", "first"), ("new-token", "new-occurrence"),
    ):
        with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
            _cycle(restarted, token_id=token_id, occurrence=occurrence)
    assert restarted[3].recover().ambiguous_running_steps == ("root",)
    assert restarted[4].count_synthetic() == reserved
    assert len(restarted[5].events()) == audited
    assert restarted[6].read_witness().event_count == linked


def test_synthetic_success_does_not_enable_replay_on_restart(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _cycle(state)
    restarted = _restart(tmp_path, state)
    assert restarted[3].recover().step_statuses == (("root", "succeeded", 2),)
    assert restarted[4].count_synthetic() == 1
    assert len(restarted[5].events()) == 1
    assert restarted[6].read_witness().event_count == 1
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _cycle(restarted, token_id="new", occurrence="new")
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False


def test_preflight_denial_is_durable_noop_after_restart(tmp_path: Path):
    state = _fixture(tmp_path)
    with pytest.raises(SyntheticMockCycleRejected, match="expired"):
        run_synthetic_mock_cycle(
            state[3], state[4], state[5], state[1], state[0],
            OneShotAuthorization("expired", state[0].request_id, 10),
            step_id="root", occurrence_id="occ_" + "a" * 64,
            now_ms=10, link_store=state[6],
        )
    restarted = _restart(tmp_path, state)
    assert restarted[3].recover().step_statuses == (("root", "pending", 0),)
    assert restarted[4].count_synthetic() == 0
    assert restarted[5].events() == []
    assert restarted[6].read_witness().event_count == 0
