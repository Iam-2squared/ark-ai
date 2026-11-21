"""Detached reservation/audit/link crash gaps cannot create replay authority.

These are disposable SQLite stores and mock backend identities only. Separate
commits cannot certify actor consent, trusted time or real exactly-once effects.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


class _NeverRun:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("mock crash recovery must never dispatch")


@pytest.mark.parametrize(
    ("phase", "expected_audits", "expected_links"),
    (
        ("after_reservation", 0, 0),
        ("after_preaction_audit", 1, 0),
        ("after_audit_link", 1, 1),
    ),
)
def test_reopened_detached_stores_do_not_resolve_crash_gap_as_approval(
    tmp_path, phase, expected_audits, expected_links,
):
    backend = _NeverRun()
    registry = ToolRegistry((
        ToolRegistration(
            "offline.write", "mock.write", Effect.WRITE, "mock-only", backend,
        ),
    ))
    call = ToolCall("offline.write", "mock.write", "private", {"fixture": 1})
    occurrence_id = "occ_" + hashlib.sha256(b"gap-occurrence").hexdigest()
    reservation_path = tmp_path / "reservation.sqlite"
    audit_path = tmp_path / "audit.sqlite"
    link_path = tmp_path / "links.sqlite"
    reservations = SyntheticOccurrenceStore(reservation_path)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(link_path)
    token = OneShotAuthorization("single-use-fixture", call.request_id, 1000)

    receipt = reservations.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=10,
    )
    if phase != "after_reservation":
        event = audit.append(call, outcome="synthetic_audit_before_mock")
        if phase == "after_audit_link":
            linked = links.link_synthetic(
                registry, call, reservations, receipt, audit, event, at_ms=15,
            )
            assert linked.dispatch_authorized is False
            assert linked.external_outcome_known is False
            assert linked.automatic_replay_authorized is False

    # Simulate process restart independently of all three committed stores.
    reopened_reservations = SyntheticOccurrenceStore(reservation_path)
    reopened_audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 20)
    reopened_links = SyntheticOccurrenceAuditLinkStore(link_path)
    assert reopened_reservations.count_synthetic() == 1
    assert len(reopened_audit.events()) == expected_audits
    witness = reopened_links.read_witness()
    assert witness.event_count == expected_links
    assert witness.last_link_at_ms == (15 if expected_links else -1)

    # Neither an absent link nor a complete local link is a permission to
    # mint another reservation or replay the unknown external outcome.
    other_occurrence = "occ_" + hashlib.sha256(b"replacement").hexdigest()
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        reopened_reservations.reserve_synthetic(
            registry, call, token, occurrence_id=other_occurrence, now_ms=20,
        )
    assert reopened_reservations.count_synthetic() == 1
    assert reopened_links.read_witness() == witness
    assert backend.calls == 0
