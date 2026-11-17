"""Corrupt intent/audit pairs must never be adopted as a retry permit.

Mutations are deliberate on-disk fault injections into disposable synthetic
SQLite files. This verifies local consistency only: no independent custody,
trusted approval, external effect or replay authorization is established.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize(
    "damage",
    ("audit_digest", "intent_chain", "audit_identity", "missing_audit"),
)
def test_cold_corrupt_pair_cannot_be_recovered_or_extended(
    tmp_path, damage: str,
) -> None:
    path = tmp_path / "synthetic-preaction-corrupt-pair.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    current = ledger.reserve(_claim("a"), retained=genesis_atomic_preaction_witness())
    assert ledger.inspect(current).occurrence_ids == (_claim("a").occurrence_id,)

    with closing(sqlite3.connect(path)) as conn, conn:
        if damage == "audit_digest":
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=? WHERE seq=1",
                ("0" * 64,),
            )
        elif damage == "intent_chain":
            conn.execute(
                "UPDATE intents SET chain_sha256=? WHERE seq=1",
                ("0" * 64,),
            )
        elif damage == "audit_identity":
            conn.execute(
                "UPDATE preaction_audit SET occurrence_id=? WHERE seq=1",
                ("occ_" + "d" * 64,),
            )
        else:
            conn.execute("DELETE FROM preaction_audit WHERE seq=1")

    with closing(sqlite3.connect(path)) as conn:
        original = (
            conn.execute(
                "SELECT seq,occurrence_id,bound_action_id,request_sha256,"
                "chain_sha256 FROM intents ORDER BY seq"
            ).fetchall(),
            conn.execute(
                "SELECT seq,occurrence_id,audit_sha256 "
                "FROM preaction_audit ORDER BY seq"
            ).fetchall(),
        )

    # Reject at every entry: constructor, retained snapshot and append.
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(current)
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(_claim("e"), retained=current)

    # A rejected attempt must neither repair the damaged evidence nor append
    # a new action intent. The original bytes remain for manual investigation.
    with closing(sqlite3.connect(path)) as conn:
        after = (
            conn.execute(
                "SELECT seq,occurrence_id,bound_action_id,request_sha256,"
                "chain_sha256 FROM intents ORDER BY seq"
            ).fetchall(),
            conn.execute(
                "SELECT seq,occurrence_id,audit_sha256 "
                "FROM preaction_audit ORDER BY seq"
            ).fetchall(),
        )
    assert after == original
