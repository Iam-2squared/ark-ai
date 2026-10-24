"""Synthetic audit sidecar must validate persisted identities without executing tools."""

import hashlib
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


class NoExecution:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic audit link may not execute a tool")


def _registry(effect=Effect.WRITE, backend_id="fixture"):
    return ToolRegistry((
        ToolRegistration("offline", "fixture", effect, backend_id, NoExecution()),
    ))


def _setup(tmp_path: Path):
    call = ToolCall("offline", "fixture", "local", {"x": 1})
    registry = _registry()
    ledger = SyntheticOccurrenceStore(tmp_path / "reservations.sqlite")
    clock = [12]
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: clock[0])
    sidecar_path = tmp_path / "links #100 %.sqlite"
    sidecar = SyntheticOccurrenceAuditLinkStore(sidecar_path)
    return registry, call, ledger, clock, audit, sidecar, sidecar_path


def _source(state, *, name="one", reserved_at=10):
    registry, call, ledger, _clock, audit, _sidecar, _path = state
    occurrence_id = "occ_" + hashlib.sha256(name.encode("utf-8")).hexdigest()
    receipt = ledger.reserve_synthetic(
        registry, call, OneShotAuthorization("token-" + name, call.request_id, 1000),
        occurrence_id=occurrence_id, now_ms=reserved_at,
    )
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    return receipt, event


def _link(state, receipt, event, *, at=15, **overrides):
    registry, call, ledger, _clock, audit, sidecar, _path = state
    values = dict(
        registry=registry, call=call, ledger=ledger,
        reservation=receipt, audit=audit, event=event, at_ms=at,
    )
    values.update(overrides)
    return sidecar.link_synthetic(**values)


def test_restart_retains_link_identity_and_all_authority_flags_denied(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    before = state[5].read_witness()
    linked = _link(state, receipt, event)
    assert linked.occurrence_id == receipt.occurrence_id
    assert linked.audit_event_id == event.event_id
    assert linked.link_hash.startswith("slink_")
    assert linked.dispatch_authorized is False
    assert linked.external_outcome_known is False
    assert linked.automatic_replay_authorized is False
    witness = SyntheticOccurrenceAuditLinkStore(state[6]).read_witness(retained=before)
    assert witness.event_count == 1
    assert witness.last_link_at_ms == 15
    assert witness.tail_hash == linked.link_hash


def test_repeated_link_is_rejected_and_keeps_first_witness(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    _link(state, receipt, event)
    previous = state[5].read_witness()
    with pytest.raises(SyntheticAuditLinkRejected, match="already linked"):
        _link(state, receipt, event, at=16)
    assert state[5].read_witness() == previous


def test_distinct_links_append_in_order(tmp_path: Path):
    state = _setup(tmp_path)
    a, event_a = _source(state)
    _link(state, a, event_a)
    state[3][0] = 25
    b, event_b = _source(state, name="two", reserved_at=20)
    result = _link(state, b, event_b, at=30)
    assert result.audit_event_id == 2
    assert state[5].read_witness().event_count == 2


def test_fabricated_receipt_does_not_link(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with pytest.raises(SyntheticAuditLinkRejected, match="stored reservation differs"):
        _link(state, replace(receipt, reserved_at_ms=9), event)
    assert state[5].read_witness().event_count == 0


def test_wrong_registry_rejected_even_if_request_matches(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with pytest.raises(SyntheticAuditLinkRejected, match="reservation binding"):
        _link(state, receipt, event, registry=_registry(backend_id="changed"))
    assert state[5].read_witness().event_count == 0


def test_read_effect_rejected_before_link(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with pytest.raises(SyntheticAuditLinkRejected, match="only synthetic WRITE"):
        _link(state, receipt, event, registry=_registry(effect=Effect.READ))


def test_other_ledger_cannot_attest_the_reservation(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    other = SyntheticOccurrenceStore(tmp_path / "other.sqlite")
    with pytest.raises(SyntheticAuditLinkRejected, match="stored reservation differs"):
        _link(state, receipt, event, ledger=other)


def test_different_call_never_links_a_matching_event(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    different = ToolCall("offline", "fixture", "local", {"x": 2})
    with pytest.raises(SyntheticAuditLinkRejected, match="reservation binding"):
        _link(state, receipt, event, call=different)


def test_non_pre_action_outcome_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, _event = _source(state)
    nonpre = state[4].append(state[1], outcome="synthetic_success_claim")
    with pytest.raises(SyntheticAuditLinkRejected, match="pre-action audit"):
        _link(state, receipt, nonpre)


def test_audit_rewrite_after_receipt_is_caught(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with sqlite3.connect(state[4].path) as conn:
        conn.execute(
            "UPDATE action_events SET outcome='changed' WHERE event_id=1"
        )
    with pytest.raises(SyntheticAuditLinkRejected, match="stored audit differs"):
        _link(state, receipt, event)
    assert state[5].read_witness().event_count == 0


def test_ledger_rewrite_after_receipt_is_caught(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with sqlite3.connect(state[2]._path) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_reservations SET bound_action_id=?",
            ("bound_" + "f" * 64,),
        )
    with pytest.raises(SyntheticAuditLinkRejected, match="stored reservation differs"):
        _link(state, receipt, event)


@pytest.mark.parametrize("bad", [-1, True, 2**63, "15"])
def test_invalid_link_clock_does_not_append(tmp_path: Path, bad):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with pytest.raises(SyntheticAuditLinkRejected, match="exact synthetic link"):
        _link(state, receipt, event, at=bad)
    assert state[5].read_witness().event_count == 0


def test_pre_audit_or_reservation_clock_cannot_be_backdated(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    with pytest.raises(SyntheticAuditLinkRejected, match="pre-action audit"):
        _link(state, receipt, event, at=11)
    assert state[5].read_witness().event_count == 0


def test_coherent_local_row_rewrite_detected_by_hash_chain(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    _link(state, receipt, event)
    with sqlite3.connect(state[6]) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_audit_links SET linked_at_ms=99"
        )
    with pytest.raises(SyntheticAuditLinkRejected, match="history changed"):
        state[5].read_witness()


def test_retained_external_witness_detects_fully_removed_row(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    _link(state, receipt, event)
    retained = state[5].read_witness()
    with sqlite3.connect(state[6]) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_audit_links")
    with pytest.raises(SyntheticAuditLinkRejected, match="retained synthetic link history"):
        state[5].read_witness(retained=retained)


def test_schema_drift_is_rejected_without_repair(tmp_path: Path):
    state = _setup(tmp_path)
    with sqlite3.connect(state[6]) as conn:
        conn.execute("ALTER TABLE synthetic_occurrence_audit_links ADD COLUMN drift TEXT")
    with pytest.raises(SyntheticAuditLinkRejected, match="schema changed"):
        state[5].read_witness()


def test_absent_sidecar_read_does_not_create_file(tmp_path: Path):
    state = _setup(tmp_path)
    state[6].unlink()
    with pytest.raises(sqlite3.OperationalError):
        state[5].read_witness()
    assert not state[6].exists()


def test_absent_sidecar_write_does_not_create_file(tmp_path: Path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    state[6].unlink()
    with pytest.raises(sqlite3.OperationalError):
        _link(state, receipt, event)
    assert not state[6].exists()
