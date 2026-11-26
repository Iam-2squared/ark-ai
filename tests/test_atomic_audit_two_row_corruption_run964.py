"""Run964: atomic intent/audit rows never self-repair into WRITE authority.

These are disposable local SQLite ledgers and inert digest-only claims.
No backend dispatch, consent, trusted clock, cross-store transaction,
external side effect or automatic replay is involved.
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


def _claim(number: int) -> AtomicIntentClaim:
    digit = f"{number:064x}"
    return AtomicIntentClaim("occ_" + digit, "bound_" + digit, digit)


def _rows(path) -> tuple[tuple[object, ...], tuple[object, ...]]:
    with sqlite3.connect(path) as conn:
        intents = tuple(conn.execute(
            "SELECT seq, occurrence_id, bound_action_id, request_sha256, "
            "chain_sha256 FROM intents ORDER BY seq"
        ).fetchall())
        audits = tuple(conn.execute(
            "SELECT seq, occurrence_id, audit_sha256 "
            "FROM preaction_audit ORDER BY seq"
        ).fetchall())
    return intents, audits


@pytest.mark.parametrize("attack", (
    "delete-audit",
    "counterfeit-audit-digest",
    "counterfeit-intent-chain",
    "counterfeit-intent-request",
))
def test_cold_atomic_ledger_quarantines_valid_width_tampering_without_repair(
    tmp_path, attack: str,
) -> None:
    path = tmp_path / "inert-corrupt-audit.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    initial = genesis_atomic_preaction_witness()
    witness = store.reserve(_claim(1), retained=initial)
    assert witness.count == 1

    with sqlite3.connect(path) as conn:
        if attack == "delete-audit":
            conn.execute("DELETE FROM preaction_audit WHERE seq=1")
        elif attack == "counterfeit-audit-digest":
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
        elif attack == "counterfeit-intent-chain":
            conn.execute(
                "UPDATE intents SET chain_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
        else:
            conn.execute(
                "UPDATE intents SET request_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
    corrupted = _rows(path)
    assert len(corrupted[0]) == 1
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        store.inspect(witness)
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(_claim(2), retained=witness)
    assert _rows(path) == corrupted
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_two_sequential_atomic_reservations_retain_exact_audit_prefix(
    tmp_path,
) -> None:
    path = tmp_path / "inert-audit-prefix.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    one = ledger.reserve(_claim(1), retained=genesis)
    two = ledger.reserve(_claim(2), retained=one)
    cold = DisconnectedAtomicPreactionLedger(path)
    snapshot = cold.inspect(two)
    assert snapshot.witness == two
    assert snapshot.occurrence_ids == (_claim(1).occurrence_id, _claim(2).occurrence_id)
    assert len(_rows(path)[0]) == len(_rows(path)[1]) == 2
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False
    with pytest.raises(AtomicPreactionRejected):
        cold.reserve(_claim(3), retained=one)
    assert len(_rows(path)[0]) == len(_rows(path)[1]) == 2
