"""Run966: persisted audit scalar type/size corruption is quarantined in place.

Disposable local SQLite only. The digest chain neither proves external effects
nor authenticates consent, identity, independent custody or replay authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(n: int) -> AtomicIntentClaim:
    digest = f"{n:064x}"
    return AtomicIntentClaim("occ_" + digest, "bound_" + digest, digest)


def _rows(path):
    with sqlite3.connect(path) as conn:
        return (
            tuple(conn.execute("SELECT * FROM intents ORDER BY seq")),
            tuple(conn.execute("SELECT * FROM preaction_audit ORDER BY seq")),
        )


@pytest.mark.parametrize(("table", "field"), (
    ("intents", "occurrence_id"),
    ("intents", "bound_action_id"),
    ("intents", "request_sha256"),
    ("intents", "chain_sha256"),
    ("preaction_audit", "occurrence_id"),
    ("preaction_audit", "audit_sha256"),
))
@pytest.mark.parametrize("mutation", ("blob", "integer", "oversized"))
def test_malformed_late_persisted_scalar_cannot_rehydrate_or_advance(
    tmp_path, table: str, field: str, mutation: str,
) -> None:
    path = tmp_path / "atomic-late-typed.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    witness = genesis_atomic_preaction_witness()
    for number in (1, 2):
        witness = ledger.reserve(_claim(number), retained=witness)
    assert witness.count == 2

    raw = (b"x" * 70 if field == "bound_action_id" else b"x" * 68
           if field == "occurrence_id" else b"x" * 64)
    corrupted = (
        sqlite3.Binary(raw) if mutation == "blob" else
        9 if mutation == "integer" else
        "x" * 8192
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE {table} SET {field}=? WHERE seq=2", (corrupted,),
        )
    before = _rows(path)
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(witness)
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(_claim(3), retained=witness)
    assert _rows(path) == before
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
