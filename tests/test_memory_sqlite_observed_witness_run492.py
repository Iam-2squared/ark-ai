"""Synthetic Memory CAS must reject nonexact SQLite-observed witnesses.

Only digest metadata is used; no private Memory content or tools are written.
"""

from __future__ import annotations

import pytest

from ark.memory import disconnected_witness_ledger as memory
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


def _epoch():
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("forged_read", (1, 2))
def test_append_rejects_equal_value_wrong_type_sqlite_witness(
    tmp_path, monkeypatch, forged_read,
):
    path = tmp_path / "witness.sqlite"
    ledger = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    genesis = memory.genesis_memory_ledger_witness()
    original = memory._inspect

    class StringSubtype(str):
        pass

    count = 0

    def forged_once(conn):
        nonlocal count
        witness, last = original(conn)
        count += 1
        if count != forged_read:
            return witness, last
        forged = memory.MemoryLedgerWitness(
            witness.epochs, StringSubtype(witness.chain_sha256),
        )
        assert forged == witness
        assert type(forged.chain_sha256) is not str
        return forged, last

    with monkeypatch.context() as patch:
        patch.setattr(memory, "_inspect", forged_once)
        with pytest.raises(
            memory.MemoryWitnessLedgerRejected, match="invalid retained witness",
        ):
            ledger.append(_epoch(), retained=genesis)

    # A pre-COMMIT refusal must not create a durable Memory witness epoch.
    assert ledger.inspect(retained=genesis) == genesis
