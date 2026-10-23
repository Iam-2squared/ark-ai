"""Read-only four-ledger recovery checks identities, never authorizes WRITE."""

import hashlib
import sqlite3
from pathlib import Path

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
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_recovery_triage import (
    SyntheticRecoveryRejected,
    review_synthetic_write_recovery,
)


class NoBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("recovery diagnosis cannot invoke a ToolBackend")


def _fixture(tmp_path: Path):
    call = ToolCall("offline", "mock", "local", {"value": 1})
    registry = ToolRegistry((
        ToolRegistration("offline", "mock", Effect.WRITE, "fixture", NoBackend()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "reservations.sqlite"
    ledger = SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    sidecar = SyntheticOccurrenceAuditLinkStore(tmp_path / "links #1 %.sqlite")
    return journal, path, ledger, audit, registry, call, sidecar


def _reserve(state, name="first"):
    _journal, _path, ledger, _audit, registry, call, _sidecar = state
    occurrence = "occ_" + hashlib.sha256(name.encode("utf-8")).hexdigest()
    return ledger.reserve_synthetic(
        registry, call, OneShotAuthorization("token-" + name, call.request_id, 999),
        occurrence_id=occurrence, now_ms=11,
    )


def _link(state, receipt):
    _journal, _path, ledger, audit, registry, call, sidecar = state
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    sidecar.link_synthetic(
        registry, call, ledger, receipt, audit, event, at_ms=13,
    )
    return event


def _review(state, **kw):
    journal, path, _ledger, audit, registry, call, sidecar = state
    return review_synthetic_write_recovery(
        journal, path, audit, registry, call,
        step_id="root", link_store=sidecar, **kw,
    )


def test_empty_sidecar_is_observed_without_claiming_permission(tmp_path: Path):
    result = _review(_fixture(tmp_path))
    assert result.link_witness.event_count == 0
    assert result.matching_audit_links == ()
    assert result.matching_occurrences == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False


def test_running_with_linked_occurrence_remains_unknown(tmp_path: Path):
    state = _fixture(tmp_path)
    state[0].append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    receipt = _reserve(state)
    event = _link(state, receipt)
    result = _review(state)
    assert result.ambiguous_write is True
    assert result.matching_occurrences == (receipt.occurrence_id,)
    assert result.matching_audit_links == ((receipt.occurrence_id, event.event_id),)
    assert result.link_witness.event_count == 1
    assert result.external_outcome_known is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_unlinked_reservation_is_never_inferred_linked(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    result = _review(state)
    assert result.matching_occurrences == (receipt.occurrence_id,)
    assert result.matching_audit_links == ()
    assert result.link_witness.event_count == 0


def test_retained_empty_prefix_accepts_new_valid_link(tmp_path: Path):
    state = _fixture(tmp_path)
    before = state[6].read_witness()
    receipt = _reserve(state)
    _link(state, receipt)
    result = _review(state, retained_link=before)
    assert result.link_witness.event_count == 1
    assert len(result.matching_audit_links) == 1


def test_retained_link_detects_deleted_locally_consistent_history(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    _link(state, receipt)
    retained = state[6].read_witness()
    with sqlite3.connect(state[6]._path) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_audit_links")
    with pytest.raises(SyntheticRecoveryRejected, match="retained.*link history"):
        _review(state, retained_link=retained)


def test_linked_audit_identity_mutation_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    _link(state, receipt)
    with sqlite3.connect(state[3].path) as conn:
        conn.execute("UPDATE action_events SET outcome='edited' WHERE event_id=1")
    with pytest.raises(SyntheticRecoveryRejected, match="sidecar link audit identity"):
        _review(state)


def test_missing_linked_reservation_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    _link(state, receipt)
    with sqlite3.connect(state[1]) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    with pytest.raises(SyntheticRecoveryRejected, match="no matching stored reservation"):
        _review(state)


def test_rewritten_link_hash_fails_before_diagnosis(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    _link(state, receipt)
    with sqlite3.connect(state[6]._path) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_audit_links SET link_hash=?",
            ("slink_" + "f" * 64,),
        )
    with pytest.raises(SyntheticAuditLinkRejected, match="link history changed"):
        _review(state)


def test_linked_audit_event_deletion_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    _link(state, receipt)
    with sqlite3.connect(state[3].path) as conn:
        conn.execute("DELETE FROM action_events")
    with pytest.raises(SyntheticRecoveryRejected, match="no matching audit event"):
        _review(state)


@pytest.mark.parametrize("invalid", [False, 3, object(), "sidecar"])
def test_invalid_sidecar_type_rejected_before_sqlite(tmp_path: Path, invalid):
    state = _fixture(tmp_path)
    with pytest.raises(SyntheticRecoveryRejected, match="retained witnesses"):
        _review(state, link_store=invalid)


def test_retained_link_requires_store(tmp_path: Path):
    state = _fixture(tmp_path)
    old = state[6].read_witness()
    with pytest.raises(SyntheticRecoveryRejected, match="retained witnesses"):
        review_synthetic_write_recovery(
            state[0], state[1], state[3], state[4], state[5],
            step_id="root", retained_link=old,
        )


def test_missing_sidecar_does_not_get_recreated(tmp_path: Path):
    state = _fixture(tmp_path)
    missing = tmp_path / "sidecar-missing.sqlite"
    state[6]._path = missing
    with pytest.raises(sqlite3.OperationalError):
        _review(state)
    assert not missing.exists()


def test_old_three_store_review_remains_backward_compatible(tmp_path: Path):
    state = _fixture(tmp_path)
    result = review_synthetic_write_recovery(
        state[0], state[1], state[3], state[4], state[5], step_id="root",
    )
    assert result.link_witness is None
    assert result.matching_audit_links == ()
    assert result.external_outcome_known is False
