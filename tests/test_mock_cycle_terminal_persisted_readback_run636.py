"""Require a newly persisted terminal journal event before a mock receipt.

All effects are disconnected fixtures; even a proven local SUCCEEDED row is
never a real-world completion, permission or replay authorization.
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
        raise AssertionError("mock-only path must never dispatch")


def _fixture(tmp_path):
    call = ToolCall("mock.write", "offline.write", "fixture", {"item": "local"})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("mock-token", call.request_id, 1_000)
    return journal, ledger, audit, registry, call, token, backend


def _cycle(state):
    journal, ledger, audit, registry, call, token, _backend = state
    return mock.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"terminal-readback").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize(
    "behavior",
    ("no_op_terminal", "persist_failed_instead", "hide_committed_terminal"),
)
def test_mock_terminal_must_be_durably_recovered(tmp_path, monkeypatch, behavior):
    state = _fixture(tmp_path)
    journal, ledger, audit, _registry, _call, _token, backend = state
    original_append = journal.append
    original_recover = journal.recover
    retained_reads = 0
    running_receipt = None

    def append_instead(step_id, target, **kwargs):
        if target is StepState.SUCCEEDED:
            if behavior == "no_op_terminal":
                return original_recover()
            if behavior == "persist_failed_instead":
                return original_append(step_id, StepState.FAILED, **kwargs)
        return original_append(step_id, target, **kwargs)

    def hide_terminal(*args, **kwargs):
        nonlocal retained_reads, running_receipt
        observed = original_recover(*args, **kwargs)
        if kwargs.get("retained") is not None:
            retained_reads += 1
            if retained_reads == 1:
                running_receipt = observed
            if retained_reads == 2:
                assert running_receipt is not None
                return running_receipt
        return observed

    with monkeypatch.context() as patch:
        if behavior == "hide_committed_terminal":
            patch.setattr(journal, "recover", hide_terminal)
        else:
            patch.setattr(journal, "append", append_instead)
        with pytest.raises(
            mock.SyntheticMockCycleRejected,
            match="durable SUCCEEDED journal transition not confirmed",
        ):
            _cycle(state)

    expected_state = (
        ("root", "running", 1) if behavior == "no_op_terminal"
        else ("root", "failed", 2) if behavior == "persist_failed_instead"
        else ("root", "succeeded", 2)
    )
    assert original_recover().step_statuses == (expected_state,)
    assert ledger.count_synthetic() == 1
    assert len(audit.events()) == 1
    assert backend.calls == 0
    with pytest.raises(mock.SyntheticMockCycleRejected, match="cannot retry"):
        _cycle(state)
    assert backend.calls == 0


def test_genuine_terminal_readback_still_has_no_external_effect(tmp_path):
    state = _fixture(tmp_path)
    receipt = _cycle(state)
    journal, ledger, audit, _registry, _call, _token, backend = state
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert ledger.count_synthetic() == 1
    assert len(audit.events()) == 1
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert backend.calls == 0
