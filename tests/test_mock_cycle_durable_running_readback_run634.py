"""A mock WRITE must re-read durable RUNNING before reserving another store.

Disconnected fixtures only: no backend execution or real authorization.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import synthetic_mock_action_cycle_review as mock
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


class ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic mock must not dispatch")


def _case(tmp_path):
    call = ToolCall("mock.write", "offline.write", "fixture", {"key": "value"})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token, backend


def _run(state):
    journal, ledger, audit, registry, call, token, _ = state
    return mock.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"durable-running-readback").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize("behavior", ("no_op", "terminal_before_reservation"))
def test_changed_journal_append_cannot_create_orphan_reservation(
    tmp_path, monkeypatch, behavior,
):
    state = _case(tmp_path)
    journal, ledger, audit, _registry, _call, _token, backend = state
    original_append = journal.append

    def replace_append(step_id, target, **kwargs):
        if behavior == "no_op":
            # A forged append return is not a durable RUNNING transition.
            return journal.recover()
        result = original_append(step_id, target, **kwargs)
        original_append(
            step_id, StepState.FAILED,
            expected_revision=1, at_ms=kwargs["at_ms"],
        )
        return result

    monkeypatch.setattr(journal, "append", replace_append)
    with pytest.raises(
        mock.SyntheticMockCycleRejected,
        match="durable RUNNING journal transition not confirmed",
    ):
        _run(state)

    assert ledger.count_synthetic() == 0
    assert audit.events() == []
    assert backend.calls == 0
    assert journal.recover().step_statuses == (
        (("root", "pending", 0),) if behavior == "no_op"
        else (("root", "failed", 2),)
    )


def test_genuine_running_readback_preserves_mock_only_and_no_replay(tmp_path):
    state = _case(tmp_path)
    receipt = _run(state)
    journal, ledger, audit, _registry, _call, _token, backend = state

    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert ledger.count_synthetic() == 1
    assert len(audit.events()) == 1
    assert backend.calls == 0
    with pytest.raises(mock.SyntheticMockCycleRejected, match="cannot retry"):
        _run(state)
    assert ledger.count_synthetic() == 1
    assert backend.calls == 0
