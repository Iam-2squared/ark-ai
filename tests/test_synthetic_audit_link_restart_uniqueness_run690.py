"""Detached audit and occurrence stores cannot reuse a committed link.

All records are synthetic local fixtures. Both journals are distinct SQLite
databases: even a linked witness proves neither consent nor external effects.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


class _NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("synthetic link must not execute a backend")


def _occurrence(value):
    return "occ_" + hashlib.sha256(value.encode("ascii")).hexdigest()


@pytest.mark.parametrize(
    "replay",
    ("same_pair", "old_occurrence_new_audit", "old_audit_new_occurrence"),
)
def test_audit_link_is_unique_across_fresh_sqlite_handles(tmp_path, replay):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "fixture.write", Effect.WRITE, "local", backend),
    ))
    call = ToolCall("mock.write", "fixture.write", "private", {"fixture": "alpha"})
    reservations = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    first = reservations.reserve_synthetic(
        registry, call, OneShotAuthorization("token-a", call.request_id, 1000),
        occurrence_id=_occurrence("a"), now_ms=10,
    )
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    genesis = links.read_witness()
    linked = links.link_synthetic(
        registry, call, reservations, first, audit, event,
        at_ms=15, retained=genesis,
    )
    assert linked.dispatch_authorized is False
    assert linked.external_outcome_known is False
    assert linked.automatic_replay_authorized is False

    if replay == "old_occurrence_new_audit":
        event = audit.append(call, outcome="synthetic_audit_before_mock")
    elif replay == "old_audit_new_occurrence":
        first = SyntheticOccurrenceStore(
            tmp_path / "occurrences.sqlite",
        ).reserve_synthetic(
            registry, call, OneShotAuthorization("token-b", call.request_id, 1000),
            occurrence_id=_occurrence("b"), now_ms=11,
        )

    witness = SyntheticOccurrenceAuditLinkStore(
        tmp_path / "links.sqlite",
    ).read_witness(retained=genesis)
    assert witness.event_count == 1
    with pytest.raises(SyntheticAuditLinkRejected, match="already linked"):
        SyntheticOccurrenceAuditLinkStore(
            tmp_path / "links.sqlite",
        ).link_synthetic(
            registry, call, SyntheticOccurrenceStore(
                tmp_path / "occurrences.sqlite",
            ), first, SQLiteActionAudit(
                tmp_path / "audit.sqlite", clock_ms=lambda: 12,
            ), event, at_ms=16, retained=witness,
        )
    assert SyntheticOccurrenceAuditLinkStore(
        tmp_path / "links.sqlite",
    ).read_witness() == witness
    assert backend.calls == 0


def test_new_occurrence_and_audit_can_link_without_releasing_first(tmp_path):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "fixture.write", Effect.WRITE, "local", backend),
    ))
    call = ToolCall("mock.write", "fixture.write", "private", {"fixture": "alpha"})
    reservations = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    before = links.read_witness()

    for index in range(2):
        reservation = reservations.reserve_synthetic(
            registry, call,
            OneShotAuthorization(f"token-{index}", call.request_id, 1000),
            occurrence_id=_occurrence(str(index)), now_ms=10 + index,
        )
        event = audit.append(call, outcome="synthetic_audit_before_mock")
        report = links.link_synthetic(
            registry, call, reservations, reservation, audit, event,
            at_ms=15 + index, retained=before,
        )
        assert report.dispatch_authorized is False
        assert report.external_outcome_known is False
        assert report.automatic_replay_authorized is False
        before = SyntheticOccurrenceAuditLinkStore(
            tmp_path / "links.sqlite",
        ).read_witness(retained=before)
        assert before.event_count == index + 1

    assert SyntheticOccurrenceStore(
        tmp_path / "occurrences.sqlite",
    ).count_synthetic() == 2
    assert len(audit.events()) == 2
    assert backend.calls == 0
