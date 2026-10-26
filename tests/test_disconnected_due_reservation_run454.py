"""Detached due reservations must be restart-safe and fail closed."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from multiprocessing import get_context

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
    DueReservationWitness,
    genesis_due_witness,
)

POLICY = "a" * 64
OTHER = "b" * 64


def store(tmp_path):
    return DisconnectedDueReservations(tmp_path / "due.sqlite3")


def _process_reserve(path, retained):
    ledger = DisconnectedDueReservations(path)
    try:
        return ledger.reserve_due(
            policy_sha256=POLICY, due_at_ms=777,
            observed_now_ms=778, retained=retained,
        ).occurrence_id
    except DueReservationRejected:
        return None


def test_processes_consume_at_most_one_due_slot(tmp_path):
    path = tmp_path / "due.sqlite3"
    ledger = DisconnectedDueReservations(path)
    with ProcessPoolExecutor(max_workers=2, mp_context=get_context("spawn")) as pool:
        outcomes = list(pool.map(
            _process_reserve, (path, path),
            (genesis_due_witness(), genesis_due_witness()),
        ))
    assert sum(item is not None for item in outcomes) == 1
    assert ledger.witness().count == 1


def test_genesis_repeated_reopen_and_receipt(tmp_path):
    ledger = store(tmp_path)
    origin = genesis_due_witness()
    assert ledger.witness() == origin
    rec = ledger.reserve_due(
        policy_sha256=POLICY, due_at_ms=1000,
        observed_now_ms=1002, retained=origin,
    )
    assert rec.occurrence_id.startswith("slot_")
    assert rec.witness.count == 1
    assert not rec.execution_authorized
    assert not rec.notification_authorized
    assert not rec.automatic_replay_authorized
    assert not rec.trusted_clock_verified
    assert not rec.witness.independent_custody_proven
    assert DisconnectedDueReservations(tmp_path / "due.sqlite3").witness() == rec.witness
    with pytest.raises(FrozenInstanceError):
        rec.occurrence_id = "changed"


def test_restart_duplicate_stale_witness_and_distinct_slots(tmp_path):
    ledger = store(tmp_path)
    old = ledger.witness()
    one = ledger.reserve_due(
        policy_sha256=POLICY, due_at_ms=10, observed_now_ms=11, retained=old,
    )
    reopened = DisconnectedDueReservations(tmp_path / "due.sqlite3")
    with pytest.raises(DueReservationRejected):
        reopened.reserve_due(
            policy_sha256=POLICY, due_at_ms=10, observed_now_ms=12, retained=one.witness,
        )
    with pytest.raises(DueReservationRejected, match="stale or rewritten"):
        reopened.reserve_due(
            policy_sha256=OTHER, due_at_ms=11, observed_now_ms=12, retained=old,
        )
    two = reopened.reserve_due(
        policy_sha256=OTHER, due_at_ms=11, observed_now_ms=12, retained=one.witness,
    )
    assert two.witness.count == 2
    assert two.occurrence_id != one.occurrence_id


@pytest.mark.parametrize("policy,due,now", [
    ("x" * 64, 1, 1), ("A" * 64, 1, 1), (True, 1, 1),
    (POLICY, True, 1), (POLICY, 1, True), (POLICY, -1, 0),
    (POLICY, 2, 1), (POLICY, 0, 60001), (POLICY, 0, 2**63),
    (POLICY, 2**63, 2**63), (POLICY, 1.0, 2),
])
def test_invalid_claims_fail_closed(tmp_path, policy, due, now):
    ledger = store(tmp_path)
    with pytest.raises(DueReservationRejected):
        ledger.reserve_due(
            policy_sha256=policy, due_at_ms=due,
            observed_now_ms=now, retained=genesis_due_witness(),
        )
    assert ledger.witness() == genesis_due_witness()


@pytest.mark.parametrize("invalid", [
    None, True, {"count": 0, "fingerprint": "a" * 64},
    DueReservationWitness(True, "a" * 64),
    DueReservationWitness(0, "A" * 64),
    DueReservationWitness(-1, "a" * 64),
    DueReservationWitness(513, "a" * 64),
])
def test_invalid_witness_fails_closed(tmp_path, invalid):
    ledger = store(tmp_path)
    with pytest.raises(DueReservationRejected):
        ledger.reserve_due(
            policy_sha256=POLICY, due_at_ms=100,
            observed_now_ms=101, retained=invalid,
        )
    assert ledger.witness() == genesis_due_witness()


def test_clock_regression_rejected(tmp_path):
    ledger = store(tmp_path)
    a = ledger.reserve_due(
        policy_sha256=POLICY, due_at_ms=100, observed_now_ms=101,
        retained=genesis_due_witness(),
    )
    with pytest.raises(DueReservationRejected, match="clock regressed"):
        ledger.reserve_due(
            policy_sha256=OTHER, due_at_ms=50,
            observed_now_ms=90, retained=a.witness,
        )
    assert ledger.witness() == a.witness


def test_two_threads_one_atomic_reservation(tmp_path):
    path = tmp_path / "due.sqlite3"
    first = DisconnectedDueReservations(path)
    retained = first.witness()

    def race(_):
        store = DisconnectedDueReservations(path)
        try:
            return store.reserve_due(
                policy_sha256=POLICY, due_at_ms=5,
                observed_now_ms=6, retained=retained,
            )
        except DueReservationRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(race, (0, 1)))
    assert sum(result is not None for result in outcomes) == 1
    assert first.witness().count == 1


def test_file_not_recreated_by_witness(tmp_path):
    path = tmp_path / "due.sqlite3"
    ledger = DisconnectedDueReservations(path)
    path.unlink()
    with pytest.raises(DueReservationRejected):
        ledger.witness()
    assert not path.exists()


def test_symbolic_paths_rejected(tmp_path):
    original = store(tmp_path)
    alias = tmp_path / "alias.sqlite3"
    alias.symlink_to(tmp_path / "due.sqlite3")
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations(alias)
    with pytest.raises(DueReservationRejected):
        original._path = alias  # only a hostile fixture can mutate the private carrier
        original.witness()


def test_schema_integrity_fails_closed(tmp_path):
    ledger = store(tmp_path)
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        conn.execute("CREATE TABLE untrusted(extra TEXT)")
    with pytest.raises(DueReservationRejected, match="schema drift"):
        ledger.witness()


def test_row_tamper_and_rewrite_guard(tmp_path):
    ledger = store(tmp_path)
    first = ledger.reserve_due(
        policy_sha256=POLICY, due_at_ms=10, observed_now_ms=11,
        retained=genesis_due_witness(),
    )
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        conn.execute("UPDATE due_reservations SET occurrence_id=?", ("slot_" + "f" * 64,))
    with pytest.raises(DueReservationRejected, match="identity"):
        ledger.witness()
    assert first.witness.count == 1


def test_complete_storage_rollback_caught_by_independent_witness(tmp_path):
    ledger = store(tmp_path)
    first = ledger.reserve_due(
        policy_sha256=POLICY, due_at_ms=10, observed_now_ms=11,
        retained=genesis_due_witness(),
    )
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        conn.execute("DELETE FROM due_reservations")
    assert ledger.witness() == genesis_due_witness()  # local hash cannot detect itself
    with pytest.raises(DueReservationRejected, match="stale or rewritten"):
        ledger.reserve_due(
            policy_sha256=POLICY, due_at_ms=10,
            observed_now_ms=12, retained=first.witness,
        )


def test_wrong_version(tmp_path):
    ledger = store(tmp_path)
    with sqlite3.connect(tmp_path / "due.sqlite3") as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(DueReservationRejected, match="schema version"):
        ledger.witness()


def test_nonexistent_parent_and_relative_rejected(tmp_path):
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations(tmp_path / "missing" / "due.db")
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations("due.db")
