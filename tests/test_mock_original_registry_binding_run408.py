"""Forged registry bindings are rejected before the first durable WRITE.

Synthetic-only, disconnected SQLite fixtures. No actual backend may execute.
"""

from dataclasses import replace
from types import SimpleNamespace

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
        raise AssertionError("mock registry binding must not dispatch")


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


@pytest.mark.parametrize("spoof", (
    "value_equal_foreign_call",
    "value_equal_foreign_registration",
    "foreign_registry_revision",
    "not_an_exact_bound_action",
))
def test_forged_registry_receipt_refused_before_any_durable_transition(
    tmp_path, monkeypatch, spoof,
):
    state = _state(tmp_path)
    real_bind = ToolRegistry.bind

    def forged(self, call):
        original = real_bind(self, call)
        if spoof == "value_equal_foreign_call":
            foreign = ToolCall(
                call.tool, call.capability, call.scope, dict(call.arguments),
            )
            assert foreign == call and foreign is not call
            return replace(original, call=foreign)
        if spoof == "value_equal_foreign_registration":
            entry = original.registration
            foreign = ToolRegistration(
                entry.name, entry.capability, entry.effect,
                entry.backend_id, entry.backend,
            )
            assert foreign == entry and foreign is not entry
            return replace(original, registration=foreign)
        if spoof == "foreign_registry_revision":
            return replace(original, registry_revision="tools_" + "0" * 64)
        return SimpleNamespace(
            registry_revision=original.registry_revision,
            call=original.call,
            registration=original.registration,
            bound_action_id=original.bound_action_id,
        )

    monkeypatch.setattr(ToolRegistry, "bind", forged)
    with pytest.raises(SyntheticMockCycleRejected, match="registry binding"):
        run_synthetic_mock_cycle(
            *state[:6], step_id="write",
            occurrence_id="occ_" + "a" * 64, now_ms=10,
        )
    assert state[0].recover().step_statuses == (("write", "pending", 0),)
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []
    assert state[6].calls == 0
