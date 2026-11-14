"""Adversarial SQLite audit alignment and coherent WAL snapshot regression.

This opt-in fixture never invokes tools and does not prove external effects,
authentic consent, independent custody, or exactly-once execution.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _setup(tmp_path: Path):
    path = tmp_path / "atomic-preaction.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    claim = AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)
    tip = ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    return path, ledger, claim, tip


def test_uncommitted_intent_change_is_invisible_to_readonly_snapshot(
    tmp_path: Path,
) -> None:
    path, ledger, claim, tip = _setup(tmp_path)
    with sqlite3.connect(path, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
        try:
            writer.execute(
                "UPDATE intents SET request_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
            snapshot = ledger.inspect(tip)
            assert snapshot.occurrence_ids == (claim.occurrence_id,)
            assert snapshot.witness == tip
            assert snapshot.tool_dispatch_authorized is False
            assert snapshot.automatic_replay_authorized is False
        finally:
            writer.rollback()
    assert DisconnectedAtomicPreactionLedger(path).inspect(tip).witness == tip


@pytest.mark.parametrize("tamper", ("bad_hash", "misaligned_row", "missing_row"))
def test_corrupt_preaction_audit_fails_closed_despite_valid_intent(
    tmp_path: Path, tamper: str,
) -> None:
    path, ledger, _claim, retained = _setup(tmp_path)
    with sqlite3.connect(path) as conn:
        if tamper == "bad_hash":
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
        else:
            conn.execute("DELETE FROM preaction_audit WHERE seq=1")
            if tamper == "misaligned_row":
                conn.execute(
                    "INSERT INTO preaction_audit VALUES (?,?,?)",
                    (99, "occ_" + "d" * 64, "e" * 64),
                )
    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(retained)
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(
            AtomicIntentClaim(
                "occ_" + "f" * 64, "bound_" + "b" * 64, "c" * 64,
            ),
            retained=retained,
        )


def test_unknown_schema_version_is_rejected_before_reservation(
    tmp_path: Path,
) -> None:
    path, ledger, _claim, retained = _setup(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(AtomicPreactionRejected, match="schema version"):
        ledger.reserve(
            AtomicIntentClaim(
                "occ_" + "d" * 64, "bound_" + "b" * 64, "c" * 64,
            ),
            retained=retained,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM intents").fetchone() == (1,)
        assert conn.execute(
            "SELECT COUNT(*) FROM preaction_audit"
        ).fetchone() == (1,)
