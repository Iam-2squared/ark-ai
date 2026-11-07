"""Read-only restart must never request a SQLite RESERVED/write lock.

These are disconnected synthetic due fixtures; neither successful inspection
nor a retained hash is permission to dispatch or notify.
"""

from __future__ import annotations

import sqlite3

from ark.agency import disconnected_due_reservation as due


def test_existing_only_and_retained_restart_use_sqlite_ro_begin(tmp_path, monkeypatch):
    path = tmp_path / "due.sqlite"
    created = due.DisconnectedDueReservations(path)
    receipt = created.reserve_due(
        policy_sha256="a" * 64, due_at_ms=10, observed_now_ms=11,
        retained=due.genesis_due_witness(),
    )
    original_connect = sqlite3.connect
    opens = []
    statements = []

    def trace_connect(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if database != ":memory:":
            opens.append(database)
            connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(due.sqlite3, "connect", trace_connect)
    opened = due.DisconnectedDueReservations(path, require_existing=True)
    restarted = due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert opened.witness() == receipt.witness
    assert restarted.witness() == receipt.witness
    assert len(opens) >= 4
    assert all(name.endswith("?mode=ro") for name in opens)
    normalized = [statement.strip().upper() for statement in statements]
    assert "BEGIN" in normalized
    assert not any(
        statement.startswith(("BEGIN IMMEDIATE", "CREATE ", "INSERT ", "UPDATE ", "DELETE "))
        for statement in normalized
    )
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False


def test_restart_inspection_remains_possible_while_another_writer_is_reserved(
    tmp_path, monkeypatch,
):
    path = tmp_path / "due.sqlite"
    created = due.DisconnectedDueReservations(path)
    witness = created.witness()
    # A SQLite RESERVED writer lock permits an ordinary reader; an attempted
    # BEGIN IMMEDIATE on the restart connection instead fails at timeout.
    original_connect = sqlite3.connect
    with original_connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")

        def fast_connect(database, *args, **kwargs):
            if database != ":memory:":
                kwargs["timeout"] = 0.05
            return original_connect(database, *args, **kwargs)

        monkeypatch.setattr(due.sqlite3, "connect", fast_connect)
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


def test_creation_mode_still_bootstraps_fixture_and_never_confers_authority(tmp_path):
    path = tmp_path / "new.sqlite"
    store = due.DisconnectedDueReservations(path)
    assert path.exists()
    assert store.witness() == due.genesis_due_witness()
    assert store.witness().independent_custody_proven is False
