"""Bounded disconnected cross-store reservation scans; no live dispatch.

A hostile/oversized SQLite fixture must not cause an unbounded recovery read.
Every callback boundary remains fail-closed even if later hashes could restore
a transiently modified input.
"""

import hashlib

import pytest

import ark.agency.synthetic_recovery_triage as recovery
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


class NeverExecute:
    def execute(self, _call):
        raise AssertionError("recovery review dispatched a real tool")


def _fixture(tmp_path):
    call = ToolCall("fixture", "write", "local", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "mock", NeverExecute()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 15)
    return journal, path, store, audit, registry, call


def _reserve(state, index):
    _journal, _path, store, _audit, registry, call = state
    store.reserve_synthetic(
        registry, call,
        OneShotAuthorization(f"synthetic-{index}", call.request_id, 1000),
        occurrence_id="occ_" + hashlib.sha256(str(index).encode()).hexdigest(),
        now_ms=11,
    )


def _review(state):
    journal, path, _store, audit, registry, call = state
    return recovery.review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="root",
    )


@pytest.mark.parametrize("limit,rows", [(0, 1), (1, 2)])
def test_direct_recovery_rejects_overbudget_reservations(
    tmp_path, monkeypatch, limit, rows,
):
    state = _fixture(tmp_path)
    for index in range(rows):
        _reserve(state, index)
    monkeypatch.setattr(recovery, "_MAX_WITNESS_ROWS", limit)
    with pytest.raises(
        recovery.SyntheticRecoveryRejected, match="reservation row budget",
    ):
        _review(state)
    assert state[2].count_synthetic() == rows


def test_exact_budget_passes_as_inert_diagnosis(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    _reserve(state, 1)
    monkeypatch.setattr(recovery, "_MAX_WITNESS_ROWS", 1)
    result = _review(state)
    assert len(result.matching_occurrences) == 1
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False


def test_per_row_digest_callback_cannot_hide_transient_input_drift(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    _reserve(state, 1)
    _reserve(state, 2)
    call = state[5]
    original = recovery._digest
    seen = []

    def callback(label, row):
        result = original(label, row)
        if label == "ARK-reservation-row-v1":
            seen.append(label)
            if len(seen) == 1:
                object.__setattr__(call, "scope", "temporarily-changed")
            elif len(seen) == 2:
                object.__setattr__(call, "scope", "local")
        return result

    monkeypatch.setattr(recovery, "_digest", callback)
    with pytest.raises(
        recovery.SyntheticRecoveryRejected, match="input|source",
    ):
        _review(state)
    assert seen == ["ARK-reservation-row-v1"]
    assert state[2].count_synthetic() == 2
