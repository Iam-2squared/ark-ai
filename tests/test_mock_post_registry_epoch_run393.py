"""Mock-only registry callbacks must not mutate pre-reservation inputs."""

import hashlib
from pathlib import Path

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


class NoBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a disconnected mock must never dispatch")


def _state(tmp_path: Path):
    call = ToolCall("offline", "synthetic", "local", {"n": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("offline", "synthetic", Effect.WRITE, "mock", NoBackend()),
    ))
    token = OneShotAuthorization("initial-token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token


def _run(state):
    journal, ledger, audit, registry, call, token = state
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root", occurrence_id="occ_" + hashlib.sha256(b"one").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize(
    "target", ("token_id", "expiry", "ledger_path", "audit_path"),
)
def test_registry_mutation_after_running_denied_before_reservation(
    tmp_path: Path, monkeypatch, target: str,
):
    state = _state(tmp_path)
    journal, ledger, audit, _registry, _call, token = state
    original_bind = ToolRegistry.bind
    calls = 0

    def inject(self, call):
        nonlocal calls
        bound = original_bind(self, call)
        calls += 1
        if calls == 4:
            if target == "token_id":
                object.__setattr__(token, "token_id", "other-token")
            elif target == "expiry":
                object.__setattr__(token, "expires_at_ms", 900)
            elif target == "ledger_path":
                ledger._path = Path(str(ledger._path))
            else:
                audit.path = Path(str(audit.path))
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", inject)
    with pytest.raises(SyntheticMockCycleRejected, match="identity"):
        _run(state)
    assert calls == 4
    assert journal.recover().ambiguous_running_steps == ("root",)
    assert ledger.count_synthetic() == 0
    assert audit.events() == []


def test_first_post_registry_callback_cannot_change_token_before_recovery(
    tmp_path: Path, monkeypatch,
):
    state = _state(tmp_path)
    journal, ledger, audit, _registry, _call, token = state
    original_bind = ToolRegistry.bind
    original_recover = SyntheticPlanJournal.recover
    calls = 0
    recoveries = 0

    def inject(self, call):
        nonlocal calls
        bound = original_bind(self, call)
        calls += 1
        if calls == 2:
            object.__setattr__(token, "token_id", "other-token")
        return bound

    def recover(self, *, retained=None):
        nonlocal recoveries
        recoveries += 1
        return original_recover(self, retained=retained)

    monkeypatch.setattr(ToolRegistry, "bind", inject)
    monkeypatch.setattr(SyntheticPlanJournal, "recover", recover)
    with pytest.raises(SyntheticMockCycleRejected, match="identity"):
        _run(state)
    assert calls == 2
    assert recoveries == 0
    assert ledger.count_synthetic() == 0
    assert audit.events() == []
    assert journal._path.exists()


def test_stable_cycle_still_only_returns_inert_mock_receipt(tmp_path: Path):
    state = _state(tmp_path)
    receipt = _run(state)
    assert receipt.mock_marker.startswith("mock_")
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert state[1].count_synthetic() == 1
