"""SQLite type-confusion and tampered-audit regression for inert preaction CAS.

Uses only disposable local files. A valid-looking row in one table is not an
authorization, a post-crash execution receipt, or proof of a real tool effect.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(seed: str = "a") -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64)


@pytest.mark.parametrize(
    ("table", "column", "replacement"),
    (
        ("intents", "occurrence_id", sqlite3.Binary(b"occ_" + b"a" * 64)),
        ("intents", "bound_action_id", sqlite3.Binary(b"bound_" + b"b" * 64)),
        ("intents", "request_sha256", sqlite3.Binary(b"c" * 64)),
        ("intents", "chain_sha256", sqlite3.Binary(b"f" * 64)),
        ("preaction_audit", "occurrence_id", sqlite3.Binary(b"occ_" + b"a" * 64)),
        ("preaction_audit", "audit_sha256", sqlite3.Binary(b"f" * 64)),
        ("preaction_audit", "occurrence_id", "occ_" + "d" * 64),
        ("preaction_audit", "audit_sha256", "f" * 64),
        ("intents", "request_sha256", "c" * 63 + "d"),
        ("intents", "chain_sha256", "f" * 64),
    ),
)
def test_tampered_storage_cannot_be_accepted_or_extended(
    tmp_path: Path, table: str, column: str, replacement: object,
) -> None:
    path = tmp_path / "disconnected-atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    before = genesis_atomic_preaction_witness()
    retained = ledger.reserve(_claim(), retained=before)

    # Only a fixed internal test table/column list is used, never user SQL.
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE {table} SET {column}=? WHERE seq=1", (replacement,),
        )

    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(retained)
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(_claim("d"), retained=retained)

    # Rejection must not append either an intent or an audit row.
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM intents").fetchone() == (1,)
        assert conn.execute("SELECT COUNT(*) FROM preaction_audit").fetchone() == (1,)


def test_restart_cannot_treat_same_file_tip_as_independent_consent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "disconnected-atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    old = genesis_atomic_preaction_witness()
    tip = ledger.reserve(_claim(), retained=old)
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path).inspect(old)

    recovered = DisconnectedAtomicPreactionLedger(path).inspect(
        AtomicPreactionWitness(tip.count, tip.tip_sha256),
    )
    assert recovered.occurrence_ids == (_claim().occurrence_id,)
    assert recovered.tool_dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert recovered.external_effect_proven is False
    assert recovered.trusted_approval_verified is False
    assert recovered.independent_custody_proven is False
