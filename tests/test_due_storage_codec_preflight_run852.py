"""Disconnected due reservation storage guards, with synthetic local SQLite only."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import disconnected_due_reservation as due


@pytest.mark.parametrize("mutation", (
    "module", "connect", "domain", "ddl", "max_rows",
))
@pytest.mark.parametrize("operation", ("create", "reopen"))
def test_due_storage_contract_drift_denied_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str, operation: str,
) -> None:
    path = tmp_path / "due.db"
    if operation == "reopen":
        due.DisconnectedDueReservations(path)
    called = []

    def forbidden_connect(*args, **kwargs):
        called.append(True)
        raise AssertionError("hostile connector reached")

    with monkeypatch.context() as patch:
        if mutation == "module":
            patch.setattr(due, "sqlite3", object())
        elif mutation == "connect":
            patch.setattr(sqlite3, "connect", forbidden_connect)
        elif mutation == "domain":
            patch.setattr(due, "_DOMAIN", b"counterfeit-domain")
        elif mutation == "ddl":
            patch.setattr(due, "_DDL", "CREATE TABLE replacement(x)")
        else:
            patch.setattr(due, "_MAX_ROWS", 1024)
        with pytest.raises(
            due.DueReservationRejected, match="digest callback authority changed",
        ):
            due.DisconnectedDueReservations(
                path, require_existing=operation == "reopen",
            )
    assert not called
    if operation == "create":
        assert not path.exists()
    else:
        assert due.DisconnectedDueReservations(path).witness().count == 0


@pytest.mark.parametrize(("field", "corrupt"), (
    ("policy_sha256", "a" * 100000),
    ("occurrence_id", "slot_" + "b" * 100000),
    ("policy_sha256", sqlite3.Binary(b"a" * 64)),
    ("due_at_ms", sqlite3.Binary(b"1")),
))
def test_due_persisted_row_bad_width_or_type_denied_before_hydration(
    tmp_path, field, corrupt,
):
    path = tmp_path / "due.db"
    ledger = due.DisconnectedDueReservations(path)
    retained = ledger.witness()
    receipt = ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=2,
        observed_now_ms=3, retained=retained,
    )
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(f"UPDATE due_reservations SET {field}=? WHERE seq=1", (corrupt,))
    with pytest.raises(
        due.DueReservationRejected, match="persisted identity width or type",
    ):
        ledger.witness()
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False


def test_due_valid_restart_preserves_denial_and_exact_receipt(tmp_path):
    path = tmp_path / "due.db"
    ledger = due.DisconnectedDueReservations(path)
    before = ledger.witness()
    receipt = ledger.reserve_due(
        policy_sha256="c" * 64, due_at_ms=21,
        observed_now_ms=22, retained=before,
    )
    restored = due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert restored.witness() == receipt.witness
    assert receipt.execution_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
