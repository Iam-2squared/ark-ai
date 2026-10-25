"""Audit-link receipt construction is a post-COMMIT local callback boundary.

A denied synthetic receipt never erases an already persisted link and never
allows backend dispatch or automatic replay. These fixtures perform no I/O
except isolated local SQLite operations.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_occurrence_audit_link_review as links
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoExecution:
    def execute(self, call):
        raise AssertionError("synthetic link must never execute tools")


def _state(tmp_path: Path):
    call = ToolCall("offline", "fixture", "local", {"a": 1})
    registry = ToolRegistry((
        ToolRegistration("offline", "fixture", Effect.WRITE, "none", NoExecution()),
    ))
    ledger = SyntheticOccurrenceStore(tmp_path / "occ.sqlite")
    receipt = ledger.reserve_synthetic(
        registry, call, OneShotAuthorization("local-token", call.request_id, 999),
        occurrence_id="occ_" + hashlib.sha256(b"occ").hexdigest(), now_ms=10,
    )
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    link = links.SyntheticOccurrenceAuditLinkStore(tmp_path / "link.sqlite")
    return registry, call, ledger, receipt, audit, event, link


def _append(state):
    registry, call, ledger, receipt, audit, event, link = state
    return link.link_synthetic(
        registry, call, ledger, receipt, audit, event, at_ms=15,
    )


def _clone(value: str) -> str:
    cloned = ("!" + value)[1:]
    assert cloned == value and cloned is not value
    return cloned


@pytest.mark.parametrize("attack", (
    "equal_occurrence", "equal_hash", "wrong_event", "foreign_object",
    "source_rebind",
))
def test_receipt_factory_attack_denies_return_but_keeps_committed_link(
    tmp_path: Path, monkeypatch, attack: str,
):
    state = _state(tmp_path)
    ledger = state[2]
    original = links.SyntheticAuditLinkReceipt

    def hostile_factory(occurrence, event_id, link_hash):
        output = original(occurrence, event_id, link_hash)
        if attack == "equal_occurrence":
            object.__setattr__(output, "occurrence_id", _clone(occurrence))
        elif attack == "equal_hash":
            object.__setattr__(output, "link_hash", _clone(link_hash))
        elif attack == "wrong_event":
            object.__setattr__(output, "audit_event_id", event_id + 1)
        elif attack == "foreign_object":
            return object()
        else:
            ledger._path = Path(str(ledger._path))
        return output

    monkeypatch.setattr(links, "SyntheticAuditLinkReceipt", hostile_factory)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="receipt|original input"):
        _append(state)
    # Once COMMIT succeeded, a rejected diagnostic output cannot undo history.
    assert state[6].read_witness().event_count == 1


def test_healthy_receipt_is_exact_and_never_authorizes_dispatch(tmp_path: Path):
    state = _state(tmp_path)
    receipt = _append(state)
    assert type(receipt) is links.SyntheticAuditLinkReceipt
    assert receipt.occurrence_id == state[3].occurrence_id
    assert receipt.audit_event_id == state[5].event_id
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert state[6].read_witness().event_count == 1
