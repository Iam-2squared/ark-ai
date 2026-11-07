"""Mock receipt provenance must match the requested inert WRITE exactly.

These are disposable SQLite fixtures; no ToolBackend can be dispatched.
A mismatching receipt after a reservation is durable leaves the journal
RUNNING/UNKNOWN rather than fabricating a successful local action.
"""

from dataclasses import replace

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("mock action cycle must not call the backend")


def _state(tmp_path):
    call = ToolCall("writer", "fixture.write", "offline", {"key": "value"})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("write", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occ.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token, backend


def _run(state):
    return run_synthetic_mock_cycle(
        *state[:6], step_id="write", occurrence_id="occ_" + "3" * 64,
        now_ms=10,
    )


@pytest.mark.parametrize(
    ("field", "wrong"),
    [
        ("occurrence_id", "occ_" + "4" * 64),
        ("registry_revision", "tools_" + "0" * 64),
        ("bound_action_id", "bound_" + "0" * 64),
        ("request_id", "act_" + "0" * 64),
        ("reserved_at_ms", 11),
        ("reserved_at_ms", True),
        ("wrong_type", None),
    ],
)
def test_forged_reservation_receipt_cannot_complete_mock_write(
    tmp_path, monkeypatch, field, wrong,
):
    state = _state(tmp_path)
    real_reserve = SyntheticOccurrenceStore.reserve_synthetic

    def misreport(self, *args, **kwargs):
        receipt = real_reserve(self, *args, **kwargs)
        if field == "wrong_type":
            return object()
        return replace(receipt, **{field: wrong})

    monkeypatch.setattr(SyntheticOccurrenceStore, "reserve_synthetic", misreport)
    with pytest.raises(SyntheticMockCycleRejected, match="reservation receipt"):
        _run(state)

    assert state[0].recover().ambiguous_running_steps == ("write",)
    assert state[1].count_synthetic() == 1
    assert state[2].events() == []
    assert state[6].calls == 0
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(state)
    assert state[1].count_synthetic() == 1


def test_original_receipt_permits_only_inert_mock_success(tmp_path):
    state = _state(tmp_path)
    receipt = _run(state)
    assert receipt.occurrence_id == "occ_" + "3" * 64
    assert not receipt.dispatch_authorized
    assert not receipt.external_outcome_known
    assert not receipt.automatic_replay_authorized
    assert state[0].recover().step_statuses == (("write", "succeeded", 2),)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    assert state[6].calls == 0
