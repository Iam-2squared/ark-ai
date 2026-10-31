"""Fail closed on equal-valued WRITE/token replacements between local commits.

No ToolBackend dispatch, trusted identity or real external action is available.
"""

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
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("disconnected WRITE fixture cannot dispatch")


def _fixture(tmp_path):
    call = ToolCall("writer", "offline.write", "local.scope", {"n": 1})
    plan = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("alpha", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 11)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("test-token-unique", call.request_id, 1000)
    return plan, ledger, audit, registry, call, token, backend


def _clone(text):
    replacement = ("!" + text)[1:]
    assert replacement == text and replacement is not text
    return replacement


def _run(state):
    plan, ledger, audit, registry, call, token, _backend = state
    return run_synthetic_mock_cycle(
        plan, ledger, audit, registry, call, token,
        step_id="alpha", occurrence_id="occ_" + "4" * 64,
        now_ms=10,
    )


@pytest.mark.parametrize("mutation", (
    "tool", "capability", "scope", "token_id", "token_request_id", "step_id",
))
def test_recovery_callback_equal_carrier_replacement_denied_before_running(
    tmp_path, monkeypatch, mutation,
):
    state = _fixture(tmp_path)
    plan, ledger, _audit, _registry, call, token, backend = state
    native = SyntheticPlanJournal.recover
    injected = []

    def recover_with_replacement(self, *args, **kwargs):
        snapshot = native(self, *args, **kwargs)
        if self is plan and not injected:
            if mutation in {"tool", "capability", "scope"}:
                object.__setattr__(
                    call, mutation, _clone(getattr(call, mutation)),
                )
            elif mutation in {"token_id", "token_request_id"}:
                field = "token_id" if mutation == "token_id" else "request_id"
                object.__setattr__(token, field, _clone(getattr(token, field)))
            else:
                step = plan._steps[0]
                object.__setattr__(step, "step_id", _clone(step.step_id))
            injected.append(mutation)
        return snapshot

    monkeypatch.setattr(SyntheticPlanJournal, "recover", recover_with_replacement)
    with pytest.raises(
        SyntheticMockCycleRejected,
        match="input identity changed between phases",
    ):
        _run(state)
    assert injected == [mutation]
    assert backend.calls == 0
    assert ledger.count_synthetic() == 0


def test_equal_token_replacement_after_running_commit_preserves_unknown(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    plan, ledger, _audit, _registry, _call, token, backend = state
    native = SyntheticPlanJournal.append
    committed = []

    def append_and_change_token(self, *args, **kwargs):
        result = native(self, *args, **kwargs)
        if self is plan and args[1] is StepState.RUNNING:
            object.__setattr__(token, "token_id", _clone(token.token_id))
            committed.append(True)
        return result

    monkeypatch.setattr(SyntheticPlanJournal, "append", append_and_change_token)
    with pytest.raises(
        SyntheticMockCycleRejected,
        match="input identity changed between phases",
    ):
        _run(state)
    assert committed == [True]
    assert plan.recover().ambiguous_running_steps == ("alpha",)
    assert ledger.count_synthetic() == 0
    assert backend.calls == 0
