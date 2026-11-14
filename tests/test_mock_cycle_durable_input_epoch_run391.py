"""Mock-only cycle must stop on drift at every durable boundary."""

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
    def execute(self, call):
        raise AssertionError("no external execution is permitted")


def _fixture(tmp_path: Path):
    call = ToolCall("synthetic", "write", "offline", {"marker": "fake"})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    registry = ToolRegistry((
        ToolRegistration("synthetic", "write", Effect.WRITE, "mock", NoBackend()),
    ))
    token = OneShotAuthorization("token", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token


def _run(state):
    return run_synthetic_mock_cycle(
        *state, step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"mock-only").hexdigest(),
        now_ms=10,
    )


@pytest.mark.parametrize("target", ["journal", "ledger", "audit", "call", "token"])
def test_recovery_callback_drift_denied_before_any_write(
    tmp_path: Path, monkeypatch, target: str,
) -> None:
    state = _fixture(tmp_path)
    journal, ledger, audit, _registry, call, token = state
    original_recover = SyntheticPlanJournal.recover
    carrier = {
        "journal": (journal, "_path"),
        "ledger": (ledger, "_path"),
        "audit": (audit, "path"),
    }
    original = None
    if target in carrier:
        holder, key = carrier[target]
        original = getattr(holder, key)

    def drift(self, *args, **kwargs):
        result = original_recover(self, *args, **kwargs)
        if target in carrier:
            holder, key = carrier[target]
            setattr(holder, key, Path(str(original)))
        elif target == "call":
            object.__setattr__(call, "scope", "other")
        else:
            object.__setattr__(token, "expires_at_ms", 900)
        return result

    monkeypatch.setattr(SyntheticPlanJournal, "recover", drift)
    with pytest.raises(SyntheticMockCycleRejected, match="identity changed"):
        _run(state)

    monkeypatch.setattr(SyntheticPlanJournal, "recover", original_recover)
    if target in carrier:
        holder, key = carrier[target]
        setattr(holder, key, original)
    elif target == "call":
        # Restore the reflected test mutation before inspecting journal
        # topology. The rejected cycle itself must never have written.
        object.__setattr__(call, "scope", "offline")
    assert journal.recover().step_statuses == (("root", "pending", 0),)
    assert ledger.count_synthetic() == 0
    assert audit.events() == []


def test_running_commit_survives_detected_path_drift_as_unknown(
    tmp_path: Path, monkeypatch,
) -> None:
    state = _fixture(tmp_path)
    journal, ledger, audit, *_ = state
    original_path = journal._path
    original_append = SyntheticPlanJournal.append

    def drift(self, *args, **kwargs):
        receipt = original_append(self, *args, **kwargs)
        self._path = Path(str(original_path))
        return receipt

    monkeypatch.setattr(SyntheticPlanJournal, "append", drift)
    with pytest.raises(SyntheticMockCycleRejected, match="identity changed"):
        _run(state)
    journal._path = original_path
    monkeypatch.setattr(SyntheticPlanJournal, "append", original_append)
    assert journal.recover().ambiguous_running_steps == ("root",)
    assert ledger.count_synthetic() == 0
    assert audit.events() == []


def test_token_drift_after_reservation_never_writes_pre_action_audit(
    tmp_path: Path, monkeypatch,
) -> None:
    state = _fixture(tmp_path)
    journal, ledger, audit, _registry, _call, token = state
    original_reserve = SyntheticOccurrenceStore.reserve_synthetic

    def drift(self, *args, **kwargs):
        result = original_reserve(self, *args, **kwargs)
        object.__setattr__(token, "expires_at_ms", 500)
        return result

    monkeypatch.setattr(SyntheticOccurrenceStore, "reserve_synthetic", drift)
    with pytest.raises(SyntheticMockCycleRejected, match="identity changed"):
        _run(state)
    assert journal.recover().ambiguous_running_steps == ("root",)
    assert ledger.count_synthetic() == 1
    assert audit.events() == []


def test_stable_mock_cycle_is_still_inert_and_nonreplayable(tmp_path: Path) -> None:
    state = _fixture(tmp_path)
    result = _run(state)
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(state)
