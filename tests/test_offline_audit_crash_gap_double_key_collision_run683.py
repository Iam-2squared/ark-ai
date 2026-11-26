"""A restarted mock WRITE reservation cannot reuse either durable uniqueness key.

The reservation, pre-action audit, and audit-link files are independent
SQLite commits; a completed local witness is not a dispatch authorization,
trusted actor/clock, or evidence of real external effects.
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
        raise AssertionError("mock recovery must not execute any backend")


@pytest.mark.parametrize("phase", ("reserved", "audited", "linked"))
@pytest.mark.parametrize("collision", ("token", "occurrence"))
def test_restarted_crash_gap_denies_both_independent_replay_keys(
    tmp_path, phase, collision,
):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "offline.write", "mock.write", Effect.WRITE, "mock-only", backend,
        ),
    ))
    call = ToolCall("offline.write", "mock.write", "private", {"fixture": 1})
    token = OneShotAuthorization("initial-offline-token", call.request_id, 1000)
    first_occurrence = "occ_" + hashlib.sha256(b"initial-occurrence").hexdigest()
    second_occurrence = "occ_" + hashlib.sha256(b"other-occurrence").hexdigest()
    reservation_path = tmp_path / "reservations.sqlite"
    audit_path = tmp_path / "audit.sqlite"
    link_path = tmp_path / "links.sqlite"

    reservations = SyntheticOccurrenceStore(reservation_path)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(link_path)
    first = reservations.reserve_synthetic(
        registry, call, token, occurrence_id=first_occurrence, now_ms=10,
    )
    if phase != "reserved":
        event = audit.append(call, outcome="synthetic_audit_before_mock")
        if phase == "linked":
            witness = links.link_synthetic(
                registry, call, reservations, first, audit, event, at_ms=15,
            )
            assert witness.dispatch_authorized is False

    restarted = SyntheticOccurrenceStore(reservation_path)
    restarted_audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 30)
    restarted_links = SyntheticOccurrenceAuditLinkStore(link_path)
    old_events = tuple(restarted_audit.events())
    old_link = restarted_links.read_witness()
    if collision == "token":
        attempted_token = token
        attempted_occurrence = second_occurrence
    else:
        attempted_token = OneShotAuthorization(
            "independent-offline-token", call.request_id, 1000,
        )
        attempted_occurrence = first_occurrence

    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        restarted.reserve_synthetic(
            registry, call, attempted_token,
            occurrence_id=attempted_occurrence, now_ms=20,
        )
    assert restarted.count_synthetic() == 1
    assert tuple(SQLiteActionAudit(audit_path, clock_ms=lambda: 30).events()) == old_events
    assert SyntheticOccurrenceAuditLinkStore(link_path).read_witness() == old_link
    assert backend.calls == 0
