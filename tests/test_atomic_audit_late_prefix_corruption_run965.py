"""Run965: forged late intent/audit rows never grant replay or self-repair.

The entire ledger is a disposable SQLite fixture; a digest is not trusted
custody, human approval, or evidence of an external side effect.
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
    value = f"{n:064x}"
    return AtomicIntentClaim("occ_" + value, "bound_" + value, value)


def _contents(path) -> tuple[tuple[tuple, ...], tuple[tuple, ...]]:
    with sqlite3.connect(path) as conn:
        intents = tuple(conn.execute(
            "SELECT * FROM intents ORDER BY seq"
        ).fetchall())
        audits = tuple(conn.execute(
            "SELECT * FROM preaction_audit ORDER BY seq"
        ).fetchall())
    return intents, audits


@pytest.mark.parametrize("seq", (2, 3))
@pytest.mark.parametrize("attack", (
    "remove-audit", "forge-audit-digest", "forge-intent-request",
    "repoint-audit-occurrence", "move-intent-sequence",
))
def test_late_corrupt_prefix_remains_unchanged_on_cold_denial(
    tmp_path, seq: int, attack: str,
) -> None:
    path = tmp_path / "late-corrupt-atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    witness = genesis_atomic_preaction_witness()
    for n in (1, 2, 3):
        witness = ledger.reserve(_claim(n), retained=witness)
    assert witness.count == 3

    with sqlite3.connect(path) as conn:
        if attack == "remove-audit":
            conn.execute("DELETE FROM preaction_audit WHERE seq=?", (seq,))
        elif attack == "forge-audit-digest":
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=? WHERE seq=?",
                ("f" * 64, seq),
            )
        elif attack == "forge-intent-request":
            conn.execute(
                "UPDATE intents SET request_sha256=? WHERE seq=?",
                ("f" * 64, seq),
            )
        elif attack == "repoint-audit-occurrence":
            conn.execute(
                "UPDATE preaction_audit SET occurrence_id=? WHERE seq=?",
                ("occ_" + "f" * 64, seq),
            )
        else:
            conn.execute(
                "UPDATE intents SET seq=? WHERE seq=?",
                (seq + 50, seq),
            )
    corrupted = _contents(path)
    assert len(corrupted[0]) == 3
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(witness)
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(_claim(4), retained=witness)
    assert _contents(path) == corrupted
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
