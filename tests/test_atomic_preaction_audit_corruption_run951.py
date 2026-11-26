"""Run951: audit-before-action local intent rows fail closed on tampering.

All fixtures are disconnected and intentionally lack execution/approval APIs.
An SQLite witness cannot attest independent custody or external exactly-once.
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


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


@pytest.mark.parametrize("tamper", (
    "missing-audit",
    "orphan-audit",
    "wrong-audit-occurrence",
    "altered-audit-digest",
    "altered-intent-request",
    "altered-intent-chain",
))
def test_cold_audit_intent_tamper_is_denied_without_repair_or_action(
    tmp_path, tamper: str,
) -> None:
    path = tmp_path / "synthetic-atomic-intent.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    first = ledger.reserve(
        _claim("a"), retained=genesis_atomic_preaction_witness(),
    )
    second = ledger.reserve(_claim("b"), retained=first)
    assert ledger.inspect(second).occurrence_ids == (
        _claim("a").occurrence_id, _claim("b").occurrence_id,
    )
    assert not hasattr(ledger, "execute")
    assert ledger.inspect(second).tool_dispatch_authorized is False

    with sqlite3.connect(path) as conn:
        if tamper == "missing-audit":
            conn.execute("DELETE FROM preaction_audit WHERE seq=2")
        elif tamper == "orphan-audit":
            conn.execute(
                "INSERT INTO preaction_audit VALUES (?,?,?)",
                (3, _claim("c").occurrence_id, "c" * 64),
            )
        elif tamper == "wrong-audit-occurrence":
            conn.execute(
                "UPDATE preaction_audit SET occurrence_id=? WHERE seq=2",
                (_claim("d").occurrence_id,),
            )
        elif tamper == "altered-audit-digest":
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=? WHERE seq=2",
                ("e" * 64,),
            )
        elif tamper == "altered-intent-request":
            conn.execute(
                "UPDATE intents SET request_sha256=? WHERE seq=2",
                ("f" * 64,),
            )
        else:
            conn.execute(
                "UPDATE intents SET chain_sha256=? WHERE seq=2",
                ("f" * 64,),
            )

    def persisted() -> tuple[object, object]:
        with sqlite3.connect(path) as conn:
            return (
                conn.execute("SELECT * FROM intents ORDER BY seq").fetchall(),
                conn.execute(
                    "SELECT * FROM preaction_audit ORDER BY seq"
                ).fetchall(),
            )

    corrupted = persisted()
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    assert persisted() == corrupted


def test_consistent_cold_audit_prefix_is_still_inert(tmp_path) -> None:
    path = tmp_path / "synthetic-intact-intents.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    previous = genesis_atomic_preaction_witness()
    for letter in "abc":
        previous = ledger.reserve(_claim(letter), retained=previous)
    cold = DisconnectedAtomicPreactionLedger(path)
    snapshot = cold.inspect(previous)
    assert snapshot.occurrence_ids == tuple(
        _claim(letter).occurrence_id for letter in "abc"
    )
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False
