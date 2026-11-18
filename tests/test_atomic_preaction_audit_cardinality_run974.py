"""Reject orphan pre-action audits before hostile row scans or Python hydration.

Local synthetic SQLite fixtures only. A matching pair is not an approval,
external effect, independent custody witness or safe automatic retry.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


def _claim(seed: int) -> atomic.AtomicIntentClaim:
    return atomic.AtomicIntentClaim(
        "occ_" + f"{seed:064x}", "bound_" + "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("corruption", ("missing", "orphan", "unbounded"))
def test_audit_cardinality_denial_precedes_payload_scan_and_join(
    tmp_path, corruption: str,
) -> None:
    path = tmp_path / "audit-cardinality.sqlite"
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(path)
    retained = ledger.reserve(
        _claim(1), retained=atomic.genesis_atomic_preaction_witness(),
    )
    assert retained.count == 1
    with sqlite3.connect(path) as conn:
        if corruption == "missing":
            conn.execute("DELETE FROM preaction_audit")
        else:
            number = 1 if corruption == "orphan" else 256
            conn.executemany(
                "INSERT INTO preaction_audit VALUES (?,?,?)",
                (
                    (n + 1, _claim(n + 1).occurrence_id, "d" * 64)
                    for n in range(1, number + 1)
                ),
            )

    sql: list[str] = []
    with closing(sqlite3.connect(path)) as conn:
        conn.set_trace_callback(sql.append)
        conn.execute("BEGIN")
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="orphan, missing or oversized pre-action audit",
        ):
            atomic._scan(conn)

    normalized = " ".join(sql).lower()
    assert "select count(*) from intents" in normalized
    assert "select count(*) from preaction_audit" in normalized
    assert "select 1 from preaction_audit where" not in normalized
    assert "select 1 from intents where" not in normalized
    assert "from intents i left join preaction_audit" not in normalized


def test_oversized_intent_set_rejected_before_audit_count_or_join(tmp_path) -> None:
    path = tmp_path / "intent-cardinality.sqlite"
    atomic.DisconnectedAtomicPreactionLedger.create(path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO intents VALUES (?,?,?,?,?)",
            (
                (n, _claim(n).occurrence_id, _claim(n).bound_action_id,
                 "c" * 64, "d" * 64)
                for n in range(1, 130)
            ),
        )
    sql: list[str] = []
    with closing(sqlite3.connect(path)) as conn:
        conn.set_trace_callback(sql.append)
        conn.execute("BEGIN")
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="intent set",
        ):
            atomic._scan(conn)
    normalized = " ".join(sql).lower()
    assert "select count(*) from intents" in normalized
    assert "select count(*) from preaction_audit" not in normalized
    assert "from intents i left join preaction_audit" not in normalized


def test_valid_pairs_still_round_trip_and_remain_inert(tmp_path) -> None:
    path = tmp_path / "clean-cardinality.sqlite"
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(path)
    prior = atomic.genesis_atomic_preaction_witness()
    first = ledger.reserve(_claim(1), retained=prior)
    second = ledger.reserve(_claim(2), retained=first)
    snapshot = atomic.DisconnectedAtomicPreactionLedger(path).inspect(second)
    assert snapshot.occurrence_ids == (
        _claim(1).occurrence_id, _claim(2).occurrence_id,
    )
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.independent_custody_proven is False
