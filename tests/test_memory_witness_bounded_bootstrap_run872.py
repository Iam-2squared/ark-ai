"""Disconnected Memory witness bootstrap: bounded catalog and planted-schema denial.

All files are disposable SQLite fixtures; no user Memory, external action,
approval, history repair, or independently authenticated evidence.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import disconnected_witness_ledger as witness


class _CatalogSpy:
    def __init__(self, connection: sqlite3.Connection, observed: list[str]) -> None:
        self.connection = connection
        self.observed = observed

    def execute(self, sql: str, *args: object):
        if sql == "SELECT name FROM sqlite_master":
            raise AssertionError("unbounded Python catalog enumeration")
        if sql == "SELECT 1 FROM sqlite_master LIMIT 1":
            self.observed.append(sql)
        return self.connection.execute(sql, *args)

    def __getattr__(self, name: str):
        return getattr(self.connection, name)


def test_fresh_witness_uses_single_row_catalog_probe(tmp_path, monkeypatch) -> None:
    path = tmp_path / "witness.sqlite"
    observed: list[str] = []
    original_open = witness.DisconnectedMemoryWitnessLedger._open

    def observing_open(self, *, read_only: bool):
        return _CatalogSpy(original_open(self, read_only=read_only), observed)

    monkeypatch.setattr(witness.DisconnectedMemoryWitnessLedger, "_open", observing_open)
    ledger = witness.DisconnectedMemoryWitnessLedger(path, create=True)
    genesis = witness.genesis_memory_ledger_witness()
    assert ledger.inspect(retained=genesis) == genesis
    assert observed == ["SELECT 1 FROM sqlite_master LIMIT 1"]


@pytest.mark.parametrize(
    ("kind", "sql"),
    (
        ("table", "CREATE TABLE planted (id INTEGER)"),
        ("view", "CREATE VIEW planted AS SELECT 1 AS id"),
    ),
)
def test_witness_bootstrap_rejects_foreign_schema_installed_after_path_preflight(
    tmp_path, monkeypatch, kind: str, sql: str,
) -> None:
    path = tmp_path / "witness.sqlite"
    original_open = witness.DisconnectedMemoryWitnessLedger._open

    def injected_open(self, *, read_only: bool):
        connection = original_open(self, read_only=read_only)
        assert read_only is False
        connection.execute(sql)
        return connection

    monkeypatch.setattr(witness.DisconnectedMemoryWitnessLedger, "_open", injected_open)
    with pytest.raises(witness.MemoryWitnessLedgerRejected, match="not empty"):
        witness.DisconnectedMemoryWitnessLedger(path, create=True)
    assert path.is_file()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        rows = connection.execute(
            "SELECT type,name FROM sqlite_master ORDER BY name"
        ).fetchall()
    assert rows == [(kind, "planted")]
