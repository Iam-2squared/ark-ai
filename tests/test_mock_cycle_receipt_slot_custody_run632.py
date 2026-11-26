"""Mock-only cycle receipts keep original slots across durable callbacks.

These fixtures never dispatch a backend and do not prove consent, external
effects, trusted time or cross-database atomicity.
"""

import hashlib

import pytest

from ark.agency import synthetic_mock_action_cycle_review as cycle
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


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("no real backend may run in this synthetic cycle")


def _case(tmp_path):
    call = ToolCall("mock.write", "offline.write", "fixture", {"n": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "journal.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token, backend


def _run(state):
    journal, ledger, audit, registry, call, token, _backend = state
    return cycle.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"run632").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize("field", (
    "step_id", "occurrence_id", "audit_event_id", "__getattribute__",
))
def test_preinstalled_result_descriptor_rejected_before_any_durable_step(
    tmp_path, monkeypatch, field,
):
    state = _case(tmp_path)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged mock receipt lookup")
        raise AssertionError("forged mock receipt descriptor executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            cycle.SyntheticMockCycleReceipt, field,
            forbidden if field == "__getattribute__" else property(forbidden),
        )
        with pytest.raises(
            cycle.SyntheticMockCycleRejected,
            match="receipt authority descriptor changed",
        ):
            _run(state)

    assert invoked == []
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []
    assert state[-1].calls == 0


@pytest.mark.parametrize("field", ("mock_marker", "__getattribute__"))
def test_postterminal_callback_rejects_receipt_descriptor_before_execution(
    tmp_path, monkeypatch, field,
):
    state = _case(tmp_path)
    appended = state[0].append
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged mock receipt lookup")
        raise AssertionError("forged mock receipt descriptor executed")

    with monkeypatch.context() as patch:
        def append(step_id, to_state, **kwargs):
            receipt = appended(step_id, to_state, **kwargs)
            if to_state is StepState.SUCCEEDED:
                patch.setattr(
                    cycle.SyntheticMockCycleReceipt, field,
                    forbidden if field == "__getattribute__"
                    else property(forbidden),
                )
            return receipt

        patch.setattr(state[0], "append", append)
        with pytest.raises(
            cycle.SyntheticMockCycleRejected,
            match="receipt authority descriptor changed",
        ):
            _run(state)

    assert invoked == []
    # The terminal journal event was committed before a postterminal
    # return check, but this is still not an external execution receipt.
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    assert state[1].count_synthetic() == 1
    assert len(state[2].events()) == 1
    assert state[-1].calls == 0


def test_unmodified_result_is_inert_and_nonreplayable(tmp_path):
    state = _case(tmp_path)
    receipt = _run(state)
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert state[-1].calls == 0
    with pytest.raises(cycle.SyntheticMockCycleRejected, match="cannot retry"):
        _run(state)
