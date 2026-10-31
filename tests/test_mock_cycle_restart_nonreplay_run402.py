"""Reopen every mock WRITE SQLite store after injected interruption.

These tests explicitly do not execute a backend. RUNNING is an ambiguous
WRITE even when locally retained reservations/audits appear consistent.
"""

import hashlib
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
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


class NeverBackend:
    def __init__(self):
        self.called = 0

    def execute(self, _call):
        self.called += 1
        raise AssertionError("disconnected mock must not execute a backend")


def _open_stores(root: Path):
    call = ToolCall("inert", "write", "local-only", {"fixture": True})
    journal = SyntheticPlanJournal(
        root / "planner.sqlite", (PlanStep("step", call),),
    )
    occurrence = SyntheticOccurrenceStore(root / "occurrence.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NeverBackend()
    registry = ToolRegistry((
        ToolRegistration("inert", "write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("local-pretend-token", call.request_id, 1000)
    return (journal, occurrence, audit, links, registry, call, token, backend)


def _cycle(state, *, fault_at=None):
    journal, occurrence, audit, links, registry, call, token, _backend = state
    return run_synthetic_mock_cycle(
        journal, occurrence, audit, registry, call, token,
        step_id="step",
        occurrence_id="occ_" + hashlib.sha256(b"reboot-test").hexdigest(),
        now_ms=10,
        fault_at=fault_at,
        link_store=links,
    )


def _counts(state):
    _journal, occurrence, audit, links, _registry, _call, _token, _backend = state
    return (
        occurrence.count_synthetic(),
        len(audit.events()),
        links.read_witness().event_count,
    )


@pytest.mark.parametrize(
    "fault_at,expected",
    (
        ("after_running", (0, 0, 0)),
        ("after_reservation", (1, 0, 0)),
        ("after_pre_action_audit", (1, 1, 0)),
        ("after_audit_link", (1, 1, 1)),
        ("after_mock_marker", (1, 1, 1)),
    ),
)
def test_restarted_stores_never_replay_ambiguous_write(
    tmp_path: Path, fault_at: str, expected: tuple[int, int, int],
):
    initial = _open_stores(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected, match="synthetic stop"):
        _cycle(initial, fault_at=fault_at)
    assert _counts(initial) == expected
    assert initial[-1].called == 0

    # Reinitialize all four SQLite fixture stores: no process-local token or
    # original PlanGraph object is used to authorize the resumed attempt.
    reopened = _open_stores(tmp_path)
    recovery = reopened[0].recover()
    assert recovery.ambiguous_running_steps == ("step",)
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False
    assert _counts(reopened) == expected

    with pytest.raises(
        SyntheticMockCycleRejected, match="not PENDING: cannot retry",
    ):
        _cycle(reopened)
    assert _counts(reopened) == expected
    assert reopened[-1].called == 0


def test_completed_local_mock_is_not_replayable_after_restart(tmp_path: Path):
    initial = _open_stores(tmp_path)
    receipt = _cycle(initial)
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert _counts(initial) == (1, 1, 1)
    assert initial[-1].called == 0

    reopened = _open_stores(tmp_path)
    assert reopened[0].recover().ambiguous_running_steps == ()
    with pytest.raises(SyntheticMockCycleRejected, match="not PENDING"):
        _cycle(reopened)
    assert _counts(reopened) == (1, 1, 1)
    assert reopened[-1].called == 0
