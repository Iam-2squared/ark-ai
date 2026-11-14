"""A newer synthetic due ledger must preserve its old reservation prefix."""

import sqlite3
from dataclasses import replace

import pytest

import ark.agency.disconnected_due_prefix_review as prefix_review
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
    genesis_due_witness,
)


def _single(tmp_path):
    path = tmp_path / "due.db"
    ledger = DisconnectedDueReservations(path)
    receipt = ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=1000, observed_now_ms=1005,
        retained=genesis_due_witness(),
    )
    return ledger, receipt.witness


def _append(ledger, retained):
    return ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=2000, observed_now_ms=2010,
        retained=retained,
    ).witness


def test_unmodified_synthetic_due_history_is_denial_only(tmp_path):
    ledger, retained = _single(tmp_path)
    result = prefix_review.review_retained_due_prefix(ledger, retained)
    assert (result.previous_count, result.current_count) == (1, 1)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.current_fingerprint == retained.fingerprint
    assert result.independently_authenticated is False
    assert result.historical_writer_proven is False
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_empty_genesis_retained_prefix_validates_later_append(tmp_path):
    ledger, _ = _single(tmp_path)
    result = prefix_review.review_retained_due_prefix(ledger, genesis_due_witness())
    assert (result.previous_count, result.current_count) == (0, 1)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"


def test_clean_append_preserves_old_prefix_without_granting_replay(tmp_path):
    ledger, retained = _single(tmp_path)
    _append(ledger, retained)
    one = prefix_review.review_retained_due_prefix(ledger, retained)
    two = prefix_review.review_retained_due_prefix(ledger, retained)
    assert one == two
    assert (one.previous_count, one.current_count) == (1, 2)
    assert one.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert one.notification_authorized is False


def test_earlier_row_rewrite_hidden_by_later_append_is_detected(tmp_path):
    ledger, retained = _single(tmp_path)
    _append(ledger, retained)
    # Still a valid occurrence and still monotonic: a mere current-head
    # comparison would not detect this rewrite of the old timestamp.
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("UPDATE due_reservations SET reserved_at_ms=1006 WHERE seq=1")
    assert ledger.witness().count == 2
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="prefix"):
        prefix_review.review_retained_due_prefix(ledger, retained)


def test_same_count_rewrite_is_detected(tmp_path):
    ledger, retained = _single(tmp_path)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("UPDATE due_reservations SET reserved_at_ms=1006")
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="prefix"):
        prefix_review.review_retained_due_prefix(ledger, retained)


def test_retained_count_rollback_is_rejected(tmp_path):
    ledger, prior = _single(tmp_path)
    newer = _append(ledger, prior)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("DELETE FROM due_reservations WHERE seq=2")
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="rolled back"):
        prefix_review.review_retained_due_prefix(ledger, newer)


def test_invalid_current_lifecycle_is_not_ignored(tmp_path):
    ledger, prior = _single(tmp_path)
    _append(ledger, prior)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("UPDATE due_reservations SET due_at_ms=-1 WHERE seq=2")
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected):
        prefix_review.review_retained_due_prefix(ledger, prior)


@pytest.mark.parametrize(
    "changes",
    [
        {"count": True},
        {"fingerprint": "invalid"},
        {"count": 2},
        {"fingerprint": "0" * 64},
    ],
)
def test_forged_or_mismatched_retained_tip_fails_closed(tmp_path, changes):
    ledger, prior = _single(tmp_path)
    altered = replace(prior, **changes)
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected):
        prefix_review.review_retained_due_prefix(ledger, altered)


def test_existing_only_reopen_cannot_create_or_retry_reservations(tmp_path):
    ledger, prior = _single(tmp_path)
    _append(ledger, prior)
    restarted = DisconnectedDueReservations(ledger._path, require_existing=True)
    report = prefix_review.review_retained_due_prefix(restarted, prior)
    assert report.current_count == 2
    assert report.automatic_replay_authorized is False


def test_read_only_review_does_not_mutate_sqlite(tmp_path):
    ledger, prior = _single(tmp_path)
    _append(ledger, prior)
    with sqlite3.connect(ledger._path) as conn:
        before = tuple(conn.iterdump())
    prefix_review.review_retained_due_prefix(ledger, prior)
    with sqlite3.connect(ledger._path) as conn:
        assert tuple(conn.iterdump()) == before


def test_source_retarget_during_validation_is_rejected(tmp_path, monkeypatch):
    ledger, prior = _single(tmp_path)
    original = prefix_review.due._inspect

    def modify_source(conn):
        result = original(conn)
        ledger._path = tmp_path / "other.db"
        return result

    monkeypatch.setattr(prefix_review.due, "_inspect", modify_source)
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="source"):
        prefix_review.review_retained_due_prefix(ledger, prior)


def test_retained_carrier_changed_during_sqlite_read_is_rejected(tmp_path, monkeypatch):
    ledger, prior = _single(tmp_path)
    original = prefix_review.due._inspect

    def mutate_witness(conn):
        result = original(conn)
        object.__setattr__(prior, "fingerprint", "0" * 64)
        return result

    monkeypatch.setattr(prefix_review.due, "_inspect", mutate_witness)
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="witness"):
        prefix_review.review_retained_due_prefix(ledger, prior)


def test_result_authority_getter_injection_is_denied(tmp_path, monkeypatch):
    ledger, prior = _single(tmp_path)
    monkeypatch.setattr(
        prefix_review.DisconnectedDuePrefixReview,
        "automatic_replay_authorized",
        property(lambda self: True),
    )
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected, match="authority"):
        prefix_review.review_retained_due_prefix(ledger, prior)


def test_reject_wrong_ledger_and_retained_witness_types(tmp_path):
    ledger, prior = _single(tmp_path)
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected):
        prefix_review.review_retained_due_prefix(object(), prior)
    with pytest.raises(prefix_review.DisconnectedDuePrefixRejected):
        prefix_review.review_retained_due_prefix(ledger, object())
    assert type(prior) is DueReservationWitness
