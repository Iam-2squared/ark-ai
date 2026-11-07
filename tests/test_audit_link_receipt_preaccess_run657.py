"""Pre-COMMIT receipt-definition custody for disconnected audit-link fixtures.

A local Python class hook is not a real-world attacker model or a backend
action. Every fixture database is disposable and no ToolBackend is dispatched.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_occurrence_audit_link_review as links
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call):
        raise AssertionError("synthetic link must not dispatch")


def _state(tmp_path: Path):
    call = ToolCall("local", "fixture", "private", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("local", "fixture", Effect.WRITE, "mock", NeverExecute()),
    ))
    reservations = SyntheticOccurrenceStore(tmp_path / "occ.sqlite")
    reservation = reservations.reserve_synthetic(
        registry,
        call,
        OneShotAuthorization("local-token", call.request_id, 999),
        occurrence_id="occ_" + hashlib.sha256(b"run657").hexdigest(),
        now_ms=10,
    )
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    link = links.SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    return registry, call, reservations, reservation, audit, event, link


def _link(state):
    registry, call, reservations, reservation, audit, event, link = state
    return link.link_synthetic(
        registry, call, reservations, reservation, audit, event, at_ms=15,
    )


@pytest.mark.parametrize("member", (
    "occurrence_id", "audit_event_id", "link_hash",
    "__init__", "__getattribute__", "__getattr__",
    "dispatch_authorized", "external_outcome_known",
    "automatic_replay_authorized",
))
def test_receipt_class_poison_denied_before_source_or_link_io(
    tmp_path: Path, monkeypatch, member: str,
):
    state = _state(tmp_path)
    called = []

    def hostile(*_args, **_kwargs):
        called.append(member)
        raise AssertionError("poisoned receipt hook executed")

    if member.startswith("__"):
        replacement = hostile
    else:
        replacement = property(hostile)
    monkeypatch.setattr(
        links.SyntheticAuditLinkReceipt, member, replacement, raising=False,
    )
    with pytest.raises(links.SyntheticAuditLinkRejected, match="receipt definition"):
        _link(state)
    assert called == []
    assert state[-1].read_witness().event_count == 0


@pytest.mark.parametrize("hash_label", (
    "ARK-synthetic-preaction-audit-v1",
    "ARK-synthetic-audit-link-v1",
))
def test_reentrant_receipt_drift_is_refused_without_persisting_link(
    tmp_path: Path, monkeypatch, hash_label: str,
):
    state = _state(tmp_path)
    original_hash = links._hash
    attacked = []
    executed = []

    def hostile(*_args, **_kwargs):
        executed.append(True)
        raise AssertionError("poisoned denial getter executed")

    def mutate_on_digest(label, fields):
        result = original_hash(label, fields)
        if label == hash_label and not attacked:
            attacked.append(label)
            monkeypatch.setattr(
                links.SyntheticAuditLinkReceipt,
                "automatic_replay_authorized",
                property(hostile),
            )
        return result

    monkeypatch.setattr(links, "_hash", mutate_on_digest)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="receipt definition"):
        _link(state)
    assert attacked == [hash_label]
    assert executed == []
    assert state[-1].read_witness().event_count == 0


def test_unmodified_receipt_is_deny_only_and_persisted(tmp_path: Path):
    state = _state(tmp_path)
    result = _link(state)
    assert type(result) is links.SyntheticAuditLinkReceipt
    assert result.occurrence_id == state[3].occurrence_id
    assert result.audit_event_id == state[5].event_id
    assert result.dispatch_authorized is False
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False
    assert state[-1].read_witness().event_count == 1
