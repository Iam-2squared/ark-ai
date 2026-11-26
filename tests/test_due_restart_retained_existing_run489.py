"""Existing-only due ledger restart requires a retained witness; no dispatch."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
    DueReservationWitness,
    genesis_due_witness,
)


def test_legacy_fixture_creation_remains_distinct(tmp_path):
    path = tmp_path / "due.sqlite"
    store = DisconnectedDueReservations(path)
    assert path.exists()
    assert store.witness() == genesis_due_witness()
    assert DisconnectedDueReservations(path, require_existing=True).witness() == (
        genesis_due_witness()
    )


@pytest.mark.parametrize("flag", [None, 1, "yes", 0, object()])
def test_existing_only_flag_requires_exact_bool(tmp_path, flag):
    path = tmp_path / "due.sqlite"
    with pytest.raises(DueReservationRejected, match="existing-only flag"):
        DisconnectedDueReservations(path, require_existing=flag)
    assert not path.exists()


def test_missing_database_must_not_be_recreated_on_restart(tmp_path):
    path = tmp_path / "lost.sqlite"
    with pytest.raises(DueReservationRejected, match="missing"):
        DisconnectedDueReservations.reopen_with_witness(
            path, retained=genesis_due_witness(),
        )
    assert not path.exists()
    with pytest.raises(DueReservationRejected, match="missing"):
        DisconnectedDueReservations(path, require_existing=True)
    assert not path.exists()


def test_deleted_database_after_reservation_is_not_recreated(tmp_path):
    path = tmp_path / "due.sqlite"
    store = DisconnectedDueReservations(path)
    receipt = store.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=10, observed_now_ms=11,
        retained=genesis_due_witness(),
    )
    path.unlink()
    with pytest.raises(DueReservationRejected, match="missing"):
        DisconnectedDueReservations.reopen_with_witness(
            path, retained=receipt.witness,
        )
    assert not path.exists()


def test_retained_restart_accepts_exact_tip_without_any_authority(tmp_path):
    path = tmp_path / "due.sqlite"
    store = DisconnectedDueReservations(path)
    receipt = store.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=10, observed_now_ms=11,
        retained=genesis_due_witness(),
    )
    reopened = DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert type(reopened) is DisconnectedDueReservations
    assert reopened.witness() == receipt.witness
    assert reopened.witness().independent_custody_proven is False
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM due_reservations").fetchone() == (1,)


def test_stale_genesis_cannot_reconcile_nonempty_database(tmp_path):
    path = tmp_path / "due.sqlite"
    store = DisconnectedDueReservations(path)
    receipt = store.reserve_due(
        policy_sha256="b" * 64,
        due_at_ms=10, observed_now_ms=11,
        retained=genesis_due_witness(),
    )
    with pytest.raises(DueReservationRejected, match="witness differs"):
        DisconnectedDueReservations.reopen_with_witness(
            path, retained=genesis_due_witness(),
        )
    assert store.witness() == receipt.witness


def test_modified_same_count_digest_denied(tmp_path):
    path = tmp_path / "due.sqlite"
    store = DisconnectedDueReservations(path)
    wrong = replace(store.witness(), fingerprint="f" * 64)
    with pytest.raises(DueReservationRejected, match="witness differs"):
        DisconnectedDueReservations.reopen_with_witness(
            path, retained=wrong,
        )
    assert store.witness() == genesis_due_witness()


def test_uninitialized_file_is_not_silently_bootstrapped_on_restart(tmp_path):
    path = tmp_path / "uninitialized.sqlite"
    path.write_bytes(b"")
    with pytest.raises(DueReservationRejected, match="uninitialized"):
        DisconnectedDueReservations.reopen_with_witness(
            path, retained=genesis_due_witness(),
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert tuple(conn.execute("SELECT name FROM sqlite_master")) == ()


@pytest.mark.parametrize("bad", [
    None, True, DueReservationWitness(True, "a" * 64),
    DueReservationWitness(0, "A" * 64),
])
def test_invalid_retained_witness_fails_before_creating_file(tmp_path, bad):
    path = tmp_path / "due.sqlite"
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations.reopen_with_witness(path, retained=bad)
    assert not path.exists()


def test_subclass_restart_cannot_override_exact_factory(tmp_path):
    class Derived(DisconnectedDueReservations):
        pass

    path = tmp_path / "due.sqlite"
    with pytest.raises(DueReservationRejected, match="exact due ledger restart class"):
        Derived.reopen_with_witness(path, retained=genesis_due_witness())
    assert not path.exists()
