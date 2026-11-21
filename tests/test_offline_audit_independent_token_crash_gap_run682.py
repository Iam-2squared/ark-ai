"""Unrelated synthetic WRITE tokens do not inherit another token's crash gap.

A separate token can be locally reserved after restart while the original
occurrence stays quarantined. Neither reservation proves human consent,
trusted clock, or whether an external effect occurred. No backend is invoked.
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


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("no actual WRITE execution permitted")


@pytest.mark.parametrize("gap", ("reserved", "audited", "linked"))
def test_independent_token_reservation_after_partial_crash_is_not_replay(
    tmp_path, gap,
):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "offline.write", "mock.write", Effect.WRITE, "mock-only", backend,
        ),
    ))
    call = ToolCall("offline.write", "mock.write", "private", {"data": 1})
    old_token = OneShotAuthorization("fixture-old", call.request_id, 1000)
    fresh_token = OneShotAuthorization("fixture-new", call.request_id, 1000)
    old_occurrence = "occ_" + hashlib.sha256(b"old").hexdigest()
    fresh_occurrence = "occ_" + hashlib.sha256(b"fresh").hexdigest()
    reservation_path = tmp_path / "reservation.sqlite"
    audit_path = tmp_path / "audit.sqlite"
    link_path = tmp_path / "links.sqlite"

    store = SyntheticOccurrenceStore(reservation_path)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(link_path)
    first = store.reserve_synthetic(
        registry, call, old_token, occurrence_id=old_occurrence, now_ms=10,
    )
    if gap != "reserved":
        event = audit.append(call, outcome="synthetic_audit_before_mock")
        if gap == "linked":
            receipt = links.link_synthetic(
                registry, call, store, first, audit, event, at_ms=15,
            )
            assert receipt.dispatch_authorized is False

    restarted = SyntheticOccurrenceStore(reservation_path)
    old_audits = len(SQLiteActionAudit(audit_path, clock_ms=lambda: 20).events())
    old_links = SyntheticOccurrenceAuditLinkStore(link_path).read_witness()
    second = restarted.reserve_synthetic(
        registry, call, fresh_token, occurrence_id=fresh_occurrence, now_ms=20,
    )
    assert second.occurrence_id == fresh_occurrence
    assert second.dispatch_authorized is False
    assert second.automatic_replay_authorized is False
    assert second.outcome_known is False
    assert restarted.count_synthetic() == 2
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        restarted.reserve_synthetic(
            registry, call, old_token, occurrence_id=old_occurrence, now_ms=21,
        )
    assert restarted.count_synthetic() == 2
    assert len(SQLiteActionAudit(audit_path, clock_ms=lambda: 30).events()) == old_audits
    assert SyntheticOccurrenceAuditLinkStore(link_path).read_witness() == old_links
    assert backend.calls == 0
