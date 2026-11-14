"""Read-only restart must never request a SQLite RESERVED/write lock.

These are disconnected synthetic due fixtures; neither successful inspection
nor a retained hash is permission to dispatch or notify.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_due_reservation as due


def test_existing_only_and_retained_restart_preserve_persisted_rows(tmp_path):
    path = tmp_path / "due.sqlite"
    created = due.DisconnectedDueReservations(path)
    receipt = created.reserve_due(
        policy_sha256="a" * 64, due_at_ms=10, observed_now_ms=11,
        retained=due.genesis_due_witness(),
    )
    with sqlite3.connect(path) as connection:
        before = tuple(connection.iterdump())

    opened = due.DisconnectedDueReservations(path, require_existing=True)
    restarted = due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert opened.witness() == receipt.witness
    assert restarted.witness() == receipt.witness
    with sqlite3.connect(path) as connection:
        assert tuple(connection.iterdump()) == before
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False


def test_restart_inspection_remains_possible_while_another_writer_is_reserved(
    tmp_path,
):
    path = tmp_path / "due.sqlite"
    created = due.DisconnectedDueReservations(path)
    witness = created.witness()
    # A RESERVED writer still permits a read-only restart. A writer-oriented
    # BEGIN IMMEDIATE in the restart would instead fail with database locked.
    with sqlite3.connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
        try:
            opened = due.DisconnectedDueReservations(path, require_existing=True)
            restarted = due.DisconnectedDueReservations.reopen_with_witness(
                path, retained=witness,
            )
            assert opened.witness() == witness
            assert restarted.witness() == witness
        finally:
            writer.rollback()
    assert path.exists()


def test_connector_instrumentation_is_denied_before_callback(
    tmp_path, monkeypatch,
):
    path = tmp_path / "due.sqlite"
    due.DisconnectedDueReservations(path)
    calls = []

    def untrusted_connect(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("must not invoke substituted connector")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", untrusted_connect)
        with pytest.raises(due.DueReservationRejected, match="digest callback authority changed"):
            due.DisconnectedDueReservations(path, require_existing=True)
    assert calls == []
    assert due.DisconnectedDueReservations(path, require_existing=True).witness() == (
        due.genesis_due_witness()
    )


def test_creation_mode_still_bootstraps_fixture_and_never_confers_authority(tmp_path):
    path = tmp_path / "new.sqlite"
    store = due.DisconnectedDueReservations(path)
    assert path.exists()
    assert store.witness() == due.genesis_due_witness()
    assert store.witness().independent_custody_proven is False
