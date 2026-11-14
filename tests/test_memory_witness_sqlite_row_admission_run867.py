"""SQL-side witness history admission precedes private row hydration."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.memory.disconnected_witness_ledger as witness


@pytest.mark.parametrize(
    "case",
    (
        "long_payload",
        "utf8_payload",
        "long_status",
        "long_chain",
        "blob_payload",
        "blob_status",
        "blob_chain",
        "too_many_rows",
    ),
)
def test_witness_row_admission_rejects_before_python_history_hydration(
    tmp_path, case,
):
    db = tmp_path / "witness.sqlite"
    witness.DisconnectedMemoryWitnessLedger(db, create=True)
    payload = "[]"
    status = "BASELINE_UNAUTHENTICATED"
    chain = "0" * 64
    if case == "long_payload":
        payload = "x" * 4097
    elif case == "utf8_payload":
        payload = "界" * 1400  # Under 4096 characters, over 4096 UTF-8 bytes.
    elif case == "long_status":
        status = "s" * 129
    elif case == "long_chain":
        chain = "a" * 65
    elif case == "blob_payload":
        payload = sqlite3.Binary(b"synthetic-private-blob")
    elif case == "blob_status":
        status = sqlite3.Binary(b"synthetic-private-blob")
    elif case == "blob_chain":
        chain = sqlite3.Binary(b"synthetic-private-blob")

    with sqlite3.connect(db) as conn:
        if case == "too_many_rows":
            conn.executemany(
                "INSERT INTO retained_memory_epochs VALUES (?,?,?,?)",
                ((seq, payload, status, chain) for seq in range(1, 258)),
            )
        else:
            conn.execute(
                "INSERT INTO retained_memory_epochs VALUES (?,?,?,?)",
                (1, payload, status, chain),
            )

    with closing(sqlite3.connect(db)) as conn:
        conn.execute("BEGIN")

        class NoHistoryHydration:
            def execute(self, query, *parameters):
                if query.startswith(
                    "SELECT seq,payload_json,status,chain_sha256 "
                ):
                    raise AssertionError("private witness rows were hydrated")
                return conn.execute(query, *parameters)

        with pytest.raises(
            witness.MemoryWitnessLedgerRejected, match="history admission"
        ):
            witness._inspect(NoHistoryHydration())
        conn.rollback()
    assert db.exists()


def test_empty_witness_ledger_still_reopens_with_genesis(tmp_path):
    db = tmp_path / "witness.sqlite"
    store = witness.DisconnectedMemoryWitnessLedger(db, create=True)
    genesis = witness.genesis_memory_ledger_witness()
    assert store.inspect(retained=genesis) == genesis
    assert witness.DisconnectedMemoryWitnessLedger(db).inspect(
        retained=genesis
    ) == genesis
