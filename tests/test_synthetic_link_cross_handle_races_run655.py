"""Concurrent synthetic audit links remain unique, restart-safe, and non-authorizing.

Two independent SQLite connections race for the same sidecar. This does not
establish cross-database atomicity, trusted consent, a backend outcome, or
permission to retry an ambiguous WRITE. No real tool is invoked.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from test_synthetic_occurrence_audit_link_run374 import _link, _setup, _source

from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


def _race(state, candidates):
    start = Barrier(2)

    def attempt(candidate):
        reservation, event = candidate
        start.wait(timeout=15)
        try:
            return ("linked", _link(state, reservation, event, at=30))
        except SyntheticAuditLinkRejected as exc:
            return ("rejected", str(exc))

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(attempt, candidates))


def test_same_receipt_racing_handles_create_one_link_and_no_dispatch(tmp_path):
    state = _setup(tmp_path)
    receipt, event = _source(state)
    genesis = state[5].read_witness()
    results = _race(state, ((receipt, event), (receipt, event)))
    assert sorted(outcome for outcome, _ in results) == ["linked", "rejected"]
    assert "already linked" in next(
        message for outcome, message in results if outcome == "rejected"
    )
    accepted = next(value for outcome, value in results if outcome == "linked")
    assert accepted.occurrence_id == receipt.occurrence_id
    assert accepted.audit_event_id == event.event_id
    assert accepted.dispatch_authorized is False
    assert accepted.external_outcome_known is False
    assert accepted.automatic_replay_authorized is False
    restarted = SyntheticOccurrenceAuditLinkStore(state[6])
    assert restarted.read_witness(retained=genesis).event_count == 1
    with sqlite3.connect(state[6]) as conn:
        assert conn.execute(
            "SELECT COUNT(*), MIN(seq), MAX(seq) "
            "FROM synthetic_occurrence_audit_links"
        ).fetchone() == (1, 1, 1)


def test_distinct_receipts_racing_handles_append_contiguous_chain(tmp_path):
    state = _setup(tmp_path)
    first = _source(state, name="race-a")
    second = _source(state, name="race-b")
    genesis = state[5].read_witness()
    results = _race(state, (first, second))
    assert [outcome for outcome, _ in results] == ["linked", "linked"]
    accepted = [value for _, value in results]
    assert {value.occurrence_id for value in accepted} == {
        first[0].occurrence_id, second[0].occurrence_id
    }
    assert all(
        value.dispatch_authorized is False
        and value.external_outcome_known is False
        and value.automatic_replay_authorized is False
        for value in accepted
    )
    restarted = SyntheticOccurrenceAuditLinkStore(state[6])
    witness = restarted.read_witness(retained=genesis)
    assert witness.event_count == 2
    with sqlite3.connect(state[6]) as conn:
        rows = conn.execute(
            "SELECT seq, occurrence_id, audit_event_id "
            "FROM synthetic_occurrence_audit_links ORDER BY seq"
        ).fetchall()
    assert [row[0] for row in rows] == [1, 2]
    assert {row[1] for row in rows} == {
        first[0].occurrence_id, second[0].occurrence_id
    }
    assert {row[2] for row in rows} == {
        first[1].event_id, second[1].event_id
    }


def test_independent_reservations_cannot_race_to_reuse_one_audit_event(tmp_path):
    state = _setup(tmp_path)
    first = _source(state, name="reservation-a")
    second = _source(state, name="reservation-b")
    results = _race(state, (first, (second[0], first[1])))
    assert sorted(outcome for outcome, _ in results) == ["linked", "rejected"]
    assert "already linked" in next(
        message for outcome, message in results if outcome == "rejected"
    )
    accepted = next(value for outcome, value in results if outcome == "linked")
    assert accepted.audit_event_id == first[1].event_id
    assert accepted.dispatch_authorized is False
    assert accepted.external_outcome_known is False
    assert accepted.automatic_replay_authorized is False
    assert SyntheticOccurrenceAuditLinkStore(state[6]).read_witness().event_count == 1
    with sqlite3.connect(state[6]) as conn:
        assert conn.execute(
            "SELECT COUNT(DISTINCT audit_event_id) "
            "FROM synthetic_occurrence_audit_links"
        ).fetchone() == (1,)
