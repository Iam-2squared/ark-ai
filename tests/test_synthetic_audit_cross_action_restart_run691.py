"""Disconnected audit-before-action links remain request-bound after restart.

Separate occurrence, audit and link SQLite files are diagnostic only.
A request swap cannot authorize another action or invoke any backend.
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


class _DisconnectedBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("fixture must never dispatch")


def _occurrence(name):
    return "occ_" + hashlib.sha256(name.encode("ascii")).hexdigest()


@pytest.mark.parametrize(
    "fault",
    (
        "other_audit",
        "other_reservation",
        "other_call",
        "pre_audit_timestamp",
    ),
)
def test_cross_action_link_swap_is_denied_and_independent_link_survives(
    tmp_path, fault,
):
    backend = _DisconnectedBackend()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "fixture.write", Effect.WRITE, "local", backend),
    ))
    calls = (
        ToolCall("mock.write", "fixture.write", "private", {"fixture": "a"}),
        ToolCall("mock.write", "fixture.write", "private", {"fixture": "b"}),
    )
    occurrence_path = tmp_path / "occurrences.sqlite"
    audit_path = tmp_path / "audit.sqlite"
    link_path = tmp_path / "links.sqlite"
    reservations = SyntheticOccurrenceStore(occurrence_path)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(link_path)
    receipts = tuple(
        reservations.reserve_synthetic(
            registry, call,
            OneShotAuthorization("token-" + suffix, call.request_id, 1000),
            occurrence_id=_occurrence(suffix), now_ms=10,
        )
        for suffix, call in zip(("a", "b"), calls, strict=True)
    )
    events = tuple(
        audit.append(call, outcome="synthetic_audit_before_mock")
        for call in calls
    )
    first = links.link_synthetic(
        registry, calls[0], reservations, receipts[0], audit, events[0],
        at_ms=15, retained=links.read_witness(),
    )
    assert first.dispatch_authorized is False
    before = SyntheticOccurrenceAuditLinkStore(link_path).read_witness()
    assert before.event_count == 1

    target_call = calls[0] if fault == "other_call" else calls[1]
    target_receipt = receipts[0] if fault == "other_reservation" else receipts[1]
    target_event = events[0] if fault == "other_audit" else events[1]
    target_time = 11 if fault == "pre_audit_timestamp" else 16
    with pytest.raises(SyntheticAuditLinkRejected):
        SyntheticOccurrenceAuditLinkStore(link_path).link_synthetic(
            registry, target_call,
            SyntheticOccurrenceStore(occurrence_path), target_receipt,
            SQLiteActionAudit(audit_path, clock_ms=lambda: 12),
            target_event, at_ms=target_time, retained=before,
        )
    assert SyntheticOccurrenceAuditLinkStore(link_path).read_witness() == before

    valid = SyntheticOccurrenceAuditLinkStore(link_path).link_synthetic(
        registry, calls[1],
        SyntheticOccurrenceStore(occurrence_path), receipts[1],
        SQLiteActionAudit(audit_path, clock_ms=lambda: 12),
        events[1], at_ms=16, retained=before,
    )
    assert valid.dispatch_authorized is False
    assert valid.external_outcome_known is False
    assert valid.automatic_replay_authorized is False
    assert SyntheticOccurrenceAuditLinkStore(link_path).read_witness().event_count == 2
    assert SyntheticOccurrenceStore(occurrence_path).count_synthetic() == 2
    assert backend.calls == 0
