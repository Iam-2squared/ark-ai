"""Synthetic audit-before-link review rejects mismatched clock and identity.

Independent reservation, action-audit, and link SQLite commits are local
diagnostics only. They cannot confer consent or real exactly-once execution.
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
        raise AssertionError("synthetic audit link must not dispatch")


@pytest.mark.parametrize(
    ("scenario", "audit_at", "link_at", "allowed"),
    (
        ("wrong_outcome", 12, 15, False),
        ("wrong_call", 12, 15, False),
        ("audit_before_reservation", 9, 15, False),
        ("audit_after_link", 16, 15, False),
        ("link_before_reservation", 12, 9, False),
        ("same_instant", 10, 10, True),
        ("normal_order", 12, 15, True),
    ),
)
def test_disconnected_link_requires_matching_audit_identity_and_time_order(
    tmp_path, scenario, audit_at, link_at, allowed,
):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("offline.write", "mock.write", Effect.WRITE, "mock-only", backend),
    ))
    call = ToolCall("offline.write", "mock.write", "private", {"fixture": 1})
    alternate_call = ToolCall(
        "offline.write", "mock.write", "private", {"fixture": 2},
    )
    token = OneShotAuthorization("one-local-token", call.request_id, 1000)
    occurrence = "occ_" + hashlib.sha256(b"independent-link-occurrence").hexdigest()
    reservations = SyntheticOccurrenceStore(tmp_path / "reservations.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: audit_at)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    reservation = reservations.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=10,
    )
    recorded_call = alternate_call if scenario == "wrong_call" else call
    outcome = (
        "synthetic_not_preaction" if scenario == "wrong_outcome"
        else "synthetic_audit_before_mock"
    )
    event = audit.append(recorded_call, outcome=outcome)
    prior = links.read_witness()

    if allowed:
        report = links.link_synthetic(
            registry, call, reservations, reservation, audit, event,
            at_ms=link_at, retained=prior,
        )
        assert report.dispatch_authorized is False
        assert report.external_outcome_known is False
        assert report.automatic_replay_authorized is False
        assert SyntheticOccurrenceAuditLinkStore(
            tmp_path / "links.sqlite",
        ).read_witness().event_count == 1
    else:
        with pytest.raises(SyntheticAuditLinkRejected):
            links.link_synthetic(
                registry, call, reservations, reservation, audit, event,
                at_ms=link_at, retained=prior,
            )
        assert SyntheticOccurrenceAuditLinkStore(
            tmp_path / "links.sqlite",
        ).read_witness() == prior
    assert reservations.count_synthetic() == 1
    assert audit.events() == [event]
    assert backend.calls == 0
