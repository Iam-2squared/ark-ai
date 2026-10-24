"""Synthetic audit receipts must remain stable across durable mock phases.

No backend is called; any rejected cycle remains an UNKNOWN, non-replayable
local WRITE regardless of independently committed audit/sidecar history.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_mock_action_cycle_review as cycle
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


class NeverBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("mock cycle may never execute a ToolBackend")


def _fixture(tmp_path: Path):
    call = ToolCall("inert", "write", "offline", {"mock": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("inert", "write", Effect.WRITE, "mock", NeverBackend()),
    ))
    token = OneShotAuthorization("fixture", call.request_id, 1000)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    return journal, occurrences, audit, registry, call, token, links


def _run(state, *, with_link=True):
    journal, occurrences, audit, registry, call, token, links = state
    return cycle.run_synthetic_mock_cycle(
        journal, occurrences, audit, registry, call, token,
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"fixture").hexdigest(),
        now_ms=10, link_store=links if with_link else None,
    )


def test_untampered_audit_receipt_keeps_synthetic_result_inert(tmp_path):
    state = _fixture(tmp_path)
    receipt = _run(state)
    assert receipt.audit_event_id == state[2].events()[0].event_id
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False


@pytest.mark.parametrize("field", ("event_id", "outcome", "request_id"))
def test_sidecar_callback_cannot_rewrite_preaction_audit_receipt(
    tmp_path, monkeypatch, field,
):
    state = _fixture(tmp_path)
    original = SyntheticOccurrenceAuditLinkStore.link_synthetic

    def link(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        audit_event = args[5]
        replacement = {
            "event_id": 42,
            "outcome": "forged-mock-result",
            "request_id": "act_" + "0" * 64,
        }[field]
        object.__setattr__(audit_event, field, replacement)
        return result

    monkeypatch.setattr(SyntheticOccurrenceAuditLinkStore, "link_synthetic", link)
    with pytest.raises(cycle.SyntheticMockCycleRejected, match="audit receipt"):
        _run(state)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[6].read_witness().event_count == 1
    assert state[2].events()[0].event_id == 1


def test_marker_hash_callback_cannot_change_audit_before_terminal_step(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    original_append = SQLiteActionAudit.append
    original_hash = cycle.hashlib.sha256
    emitted = []
    modified = []

    def append(self, *args, **kwargs):
        result = original_append(self, *args, **kwargs)
        emitted.append(result)
        return result

    def sha256(data=b""):
        result = original_hash(data)
        if data.startswith(b"ARK-no-action-mock-v1"):
            object.__setattr__(emitted[0], "outcome", "tampered")
            modified.append(True)
        return result

    monkeypatch.setattr(SQLiteActionAudit, "append", append)
    monkeypatch.setattr(cycle.hashlib, "sha256", sha256)
    with pytest.raises(cycle.SyntheticMockCycleRejected, match="audit receipt"):
        _run(state, with_link=False)
    assert modified
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[2].events()[0].outcome == "synthetic_audit_before_mock"
