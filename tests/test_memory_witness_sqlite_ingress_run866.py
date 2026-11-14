"""Disconnected Memory witness SQLite admission: bounded, non-authorizing fixtures."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

import ark.memory.disconnected_witness_ledger as ledger


@pytest.mark.parametrize("invalid", ["nul", "encoded_length"])
def test_invalid_path_rejected_before_any_filesystem_inspection(
    tmp_path, monkeypatch, invalid,
):
    candidate = (
        tmp_path / "bad\x00name.sqlite"
        if invalid == "nul"
        else tmp_path / ("界" * 1500 + ".sqlite")
    )
    # Do not consult the private fixture tree after a lexical/path-byte fail.
    visits = []
    original = Path.lstat

    def observed_lstat(self):
        visits.append(self)
        return original(self)

    monkeypatch.setattr(Path, "lstat", observed_lstat)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="path"):
        ledger.DisconnectedMemoryWitnessLedger(candidate, create=True)
    assert visits == []


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_create_refuses_orphan_sqlite_companions(tmp_path, suffix):
    db = tmp_path / "witness.sqlite"
    sidecar = db.with_name(db.name + suffix)
    sidecar.write_bytes(b"synthetic-orphan")
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="sidecar"):
        ledger.DisconnectedMemoryWitnessLedger(db, create=True)
    assert not db.exists()
    assert sidecar.read_bytes() == b"synthetic-orphan"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_reopen_refuses_nonregular_sidecar_without_repair(tmp_path, suffix):
    db = tmp_path / "witness.sqlite"
    store = ledger.DisconnectedMemoryWitnessLedger(db, create=True)
    genesis = ledger.genesis_memory_ledger_witness()
    assert store.inspect(retained=genesis) == genesis
    companion = db.with_name(db.name + suffix)
    companion.mkdir()
    try:
        with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="sidecar"):
            ledger.DisconnectedMemoryWitnessLedger(db)
        assert companion.is_dir()
    finally:
        companion.rmdir()


@pytest.mark.parametrize("case", ("extra_object", "oversized_ddl"))
def test_schema_preflight_rejects_unbounded_catalog_without_repair(
    tmp_path, case,
):
    db = tmp_path / "witness.sqlite"
    ledger.DisconnectedMemoryWitnessLedger(db, create=True)
    with sqlite3.connect(db) as conn:
        if case == "extra_object":
            conn.execute("CREATE TABLE unexpected (id INTEGER)")
        else:
            conn.execute("DROP TABLE retained_memory_epochs")
            conn.execute(
                "CREATE TABLE retained_memory_epochs ("
                "seq INTEGER PRIMARY KEY, payload_json TEXT NOT NULL, "
                "status TEXT NOT NULL, chain_sha256 TEXT NOT NULL, "
                "oversized_" + ("a" * 5000) + " INTEGER)"
            )
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="schema drift"):
        ledger.DisconnectedMemoryWitnessLedger(db)
    assert db.exists()


@pytest.mark.parametrize("rows", [
    [("ok",), ("synthetic-corruption",)],
    [("synthetic-corruption",)],
    [],
])
def test_schema_quick_check_hydrates_at_most_two_diagnostics(tmp_path, rows):
    db = tmp_path / "witness.sqlite"
    ledger.DisconnectedMemoryWitnessLedger(db, create=True)
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("BEGIN")

        class Cursor:
            def fetchmany(self, count):
                assert count == 2
                return rows

            def fetchall(self):
                raise AssertionError("unbounded quick_check hydration")

        class Connection:
            def execute(self, sql):
                if sql == "PRAGMA quick_check":
                    return Cursor()
                return conn.execute(sql)

        with pytest.raises(
            ledger.MemoryWitnessLedgerRejected, match="integrity failed"
        ):
            ledger._schema(Connection())
        conn.rollback()
