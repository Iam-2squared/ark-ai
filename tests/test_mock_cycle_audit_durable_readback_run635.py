"""Require a newly committed audit row before mock WRITE can finish.

These fixtures cannot dispatch external tools; a forged callback leaves an
UNKNOWN write for manual inspection and never permits automatic replay.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import synthetic_mock_action_cycle_review as mock
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    ActionAuditEvent,
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic mock dispatched a backend")


def _case(tmp_path):
    call = ToolCall("mock.write", "offline.write", "fixture", {"key": "value"})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token, backend


def _run(case):
    journal, ledger, audit, registry, call, token, _backend = case
    return mock.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"readback-audit").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize("kind", ("fresh_no_op", "reused_old_row", "hidden_committed_row"))
def test_mock_cycle_rejects_unproven_audit_without_marking_success(
    tmp_path, monkeypatch, kind,
):
    case = _case(tmp_path)
    journal, ledger, audit, _registry, call, _token, backend = case
    original_append = audit.append
    original_events = audit.events

    if kind == "reused_old_row":
        prior = original_append(call, outcome="synthetic_audit_before_mock")
    else:
        prior = ActionAuditEvent(
            1, call.request_id, call.tool, call.capability, call.scope,
            call.arguments_sha256, "synthetic_audit_before_mock", 12,
        )

    if kind in ("fresh_no_op", "reused_old_row"):
        monkeypatch.setattr(audit, "append", lambda *_args, **_kwargs: prior)
    else:
        # A durable append happened, but its claimed post-commit readback is
        # not present in the callback's result. Deny rather than trust it.
        monkeypatch.setattr(
            audit, "events", lambda **_kwargs: [],
        )
    with pytest.raises(
        mock.SyntheticMockCycleRejected,
        match="durable pre-action audit transition not confirmed",
    ):
        _run(case)

    stored = original_events()
    assert len(stored) == (1 if kind != "fresh_no_op" else 0)
    assert ledger.count_synthetic() == 1
    assert journal.recover().step_statuses == (("root", "running", 1),)
    assert backend.calls == 0
    with pytest.raises(mock.SyntheticMockCycleRejected, match="cannot retry"):
        _run(case)
    assert backend.calls == 0


def test_real_committed_pre_action_audit_allows_only_local_mock_marker(tmp_path):
    case = _case(tmp_path)
    receipt = _run(case)
    journal, ledger, audit, _registry, call, _token, backend = case

    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert ledger.count_synthetic() == 1
    stored = audit.events()
    assert len(stored) == 1
    assert stored[0].request_id == call.request_id
    assert stored[0].event_id == receipt.audit_event_id
    assert stored[0].outcome == "synthetic_audit_before_mock"
    assert backend.calls == 0
