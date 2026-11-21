"""Offline atomic pre-action SQLite UTF-8 width and exact-type regression.

No audit here is authenticated, and no fixture can authorize tool dispatch.
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


def _seed(tmp_path):
    path = tmp_path / "preaction.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    claim = AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)
    witness = ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    return path, ledger, witness


@pytest.mark.parametrize(
    ("table", "column", "width"),
    (
        ("intents", "occurrence_id", 68),
        ("intents", "bound_action_id", 70),
        ("intents", "request_sha256", 64),
        ("intents", "chain_sha256", 64),
        ("preaction_audit", "occurrence_id", 68),
        ("preaction_audit", "audit_sha256", 64),
    ),
)
def test_fixed_codepoint_width_cannot_bypass_native_byte_admission(
    tmp_path, table, column, width,
):
    path, ledger, retained = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE {table} SET {column}=? WHERE seq=1",
            ("é" * width,),
        ).rowcount == 1
        # This used to pass the old length(TEXT) admission predicate.
        text_size, byte_size = conn.execute(
            f"SELECT length({column}),length(CAST({column} AS BLOB)) "
            f"FROM {table} WHERE seq=1"
        ).fetchone()
        assert text_size == width and byte_size == 2 * width

    with pytest.raises(AtomicPreactionRejected, match="width or type"):
        DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected, match="width or type"):
        ledger.inspect(retained)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM intents").fetchone() == (1,)
        assert conn.execute("SELECT COUNT(*) FROM preaction_audit").fetchone() == (1,)


def test_ascii_intent_audit_restart_remains_inert(tmp_path):
    path, ledger, witness = _seed(tmp_path)
    original = ledger.inspect(witness)
    recovered = DisconnectedAtomicPreactionLedger(path).inspect(witness)
    assert recovered == original
    assert recovered.tool_dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert recovered.external_effect_proven is False
    assert not hasattr(ledger, "execute")
