"""Verify cross-SQLite mock link readback and post-terminal audit custody.

Only temporary fixture stores are mutated. No backend execution is possible;
rejected post-COMMIT paths remain manual-only even if a local journal is terminal.
"""

from __future__ import annotations

import hashlib
import sqlite3

import pytest

from ark.agency import synthetic_mock_action_cycle_review as mock
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkReceipt,
    SyntheticOccurrenceAuditLinkStore,
)


class ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("a disconnected mock must never execute a backend")


def _case(tmp_path):
    call = ToolCall("mock.write", "offline.write", "fixture", {"value": "local"})
    journal = SyntheticPlanJournal(tmp_path / "journal.sqlite", (PlanStep("root", call),))
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("fixture-token", call.request_id, 1000)
    return journal, ledger, audit, links, registry, call, token, backend


def _run(case):
    journal, ledger, audit, links, registry, call, token, _backend = case
    return mock.run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root", occurrence_id="occ_" + hashlib.sha256(b"sidecar").hexdigest(),
        now_ms=10, link_store=links,
    )


@pytest.mark.parametrize("kind", ("no_op", "forged_receipt", "forged_new_tip"))
def test_mock_must_prove_one_new_link_before_terminal(tmp_path, monkeypatch, kind):
    case = _case(tmp_path)
    journal, ledger, audit, links, _registry, _call, _token, backend = case
    original = links.link_synthetic

    def link_callback(*args, **kwargs):
        if kind == "no_op":
            return None
        if kind == "forged_new_tip":
            return SyntheticAuditLinkReceipt(
                kwargs.get("unused", "occ_" + hashlib.sha256(b"sidecar").hexdigest()),
                1, "slink_" + "0" * 64,
            )
        valid = original(*args, **kwargs)
        return SyntheticAuditLinkReceipt("occ_" + "f" * 64, valid.audit_event_id, valid.link_hash)

    monkeypatch.setattr(links, "link_synthetic", link_callback)
    match = (
        "durable synthetic audit link transition not confirmed"
        if kind == "forged_new_tip"
        else "synthetic audit link receipt differs"
    )
    with pytest.raises(mock.SyntheticMockCycleRejected, match=match):
        _run(case)
    assert journal.recover().step_statuses == (("root", "running", 1),)
    assert ledger.count_synthetic() == 1
    assert len(audit.events()) == 1
    assert links.read_witness().event_count == (1 if kind == "forged_receipt" else 0)
    with pytest.raises(mock.SyntheticMockCycleRejected, match="cannot retry"):
        _run(case)
    assert backend.calls == 0


def test_terminal_callback_cannot_invalidate_preaction_audit(tmp_path, monkeypatch):
    case = _case(tmp_path)
    journal, ledger, audit, links, _registry, _call, _token, backend = case
    append = journal.append

    def terminal_mutates_audit(step_id, target, **kwargs):
        receipt = append(step_id, target, **kwargs)
        if target is StepState.SUCCEEDED:
            # Mutate ONLY ephemeral, dedicated test SQLite data to reproduce
            # a distinct-store writer between audit and journal commits.
            with sqlite3.connect(audit.path) as conn:
                conn.execute(
                    "UPDATE action_events SET outcome=? WHERE event_id=1",
                    ("other-event",),
                )
        return receipt

    monkeypatch.setattr(journal, "append", terminal_mutates_audit)
    with pytest.raises(
        mock.SyntheticMockCycleRejected,
        match="durable pre-action audit transition not confirmed",
    ):
        _run(case)
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert ledger.count_synthetic() == 1
    assert links.read_witness().event_count == 1
    with pytest.raises(mock.SyntheticMockCycleRejected, match="cannot retry"):
        _run(case)
    assert backend.calls == 0


def test_sidecar_readback_fails_closed_after_terminal_callback(tmp_path, monkeypatch):
    case = _case(tmp_path)
    journal, ledger, _audit, links, _registry, _call, _token, backend = case
    append = journal.append
    read_witness = links.read_witness
    before = read_witness()

    def terminal_hides_link(step_id, target, **kwargs):
        receipt = append(step_id, target, **kwargs)
        if target is StepState.SUCCEEDED:
            monkeypatch.setattr(links, "read_witness", lambda **_kwargs: before)
        return receipt

    monkeypatch.setattr(journal, "append", terminal_hides_link)
    with pytest.raises(
        mock.SyntheticMockCycleRejected,
        match="synthetic audit link changed after journal terminal",
    ):
        _run(case)
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert read_witness().event_count == 1
    assert backend.calls == 0


def test_committed_link_and_audit_leave_no_external_authority(tmp_path):
    case = _case(tmp_path)
    receipt = _run(case)
    journal, ledger, audit, links, _registry, _call, _token, backend = case
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert ledger.count_synthetic() == 1
    assert links.read_witness().event_count == 1
    assert len(audit.events()) == 1
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert backend.calls == 0
