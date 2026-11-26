"""Private-memory witness catalog budget under synthetic SQLite corruption.

Only a disposable digest-only fixture; this is not retained witness attestation,
consent, evidence that memory was disclosed, or tool execution permission.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import disconnected_witness_ledger as witness


class _NoSchemaHydration:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.hydrated = False

    def execute(self, statement: str):
        if statement.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            self.hydrated = True
            pytest.fail("oversized witness catalog loaded into Python")
        return self.conn.execute(statement)


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("name", "n" * 4200),
        ("tbl_name", "t" * 4200),
        ("type", "x" * 4200),
        ("name", "界" * 1400),
    ),
)
def test_memory_witness_catalog_bytes_denied_before_hydration(
    tmp_path, field: str, forged: str,
) -> None:
    ledger = witness.DisconnectedMemoryWitnessLedger(
        tmp_path / "memory-witness.sqlite", create=True,
    )
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? "
            "WHERE name='retained_memory_epochs'",
            (forged,),
        )
        guard = _NoSchemaHydration(conn)
        with pytest.raises(witness.MemoryWitnessLedgerRejected, match="schema drift"):
            witness._schema(guard)
        assert guard.hydrated is False


def test_memory_witness_cumulative_catalog_budget(tmp_path) -> None:
    ledger = witness.DisconnectedMemoryWitnessLedger(
        tmp_path / "memory-witness.sqlite", create=True,
    )
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? "
            "WHERE name='retained_memory_epochs'",
            ("n" * 2200, "t" * 2200),
        )
        guard = _NoSchemaHydration(conn)
        with pytest.raises(witness.MemoryWitnessLedgerRejected, match="schema drift"):
            witness._schema(guard)
        assert guard.hydrated is False


def test_clean_memory_witness_cold_read_remains_deny_only(tmp_path) -> None:
    path = tmp_path / "memory-witness.sqlite"
    witness.DisconnectedMemoryWitnessLedger(path, create=True)
    prior = witness.genesis_memory_ledger_witness()
    cold = witness.DisconnectedMemoryWitnessLedger(path)
    observed = cold.inspect(retained=prior)
    assert observed == prior
    assert observed.custody_authenticated is False
    assert observed.memory_disclosure_authorized is False
    assert observed.dispatch_authorized is False
