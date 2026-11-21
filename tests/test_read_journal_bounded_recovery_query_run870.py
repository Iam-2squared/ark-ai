"""Detached READ recovery scans a bounded receipt page under one snapshot.

All identifiers/digests are synthetic. No live ToolBackend or replay authority.
"""
from __future__ import annotations

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadReceipt,
    genesis_witness,
)


def _receipt(index):
    return ReadReceipt(
        "req_" + "a" * 32, "step_" + f"{index:016x}",
        "math.sum", "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("count", (0, 1, 3))
def test_read_recovery_sql_is_bounded_and_preserves_digest_only_order(tmp_path, count):
    path = tmp_path / "read.sqlite"
    with DisconnectedReadJournal.create(path) as writer:
        witness = genesis_witness()
        for i in range(count):
            witness = writer.append(_receipt(i + 1), witness)

    sql = []
    with DisconnectedReadJournal.open(path) as reader:
        reader._connection.set_trace_callback(sql.append)
        snapshot = reader.recover_receipts(witness)

    queries = [s for s in sql if "SELECT request_id,step_id,operation," in s]
    assert len(queries) == 1
    assert "LIMIT 129" in queries[0]
    assert snapshot.receipts == tuple(_receipt(i + 1) for i in range(count))
    assert snapshot.witness == witness
    assert snapshot.dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.independent_custody_proven is False


def test_read_recovery_stale_tip_stays_manual_only_after_append(tmp_path):
    path = tmp_path / "read.sqlite"
    with DisconnectedReadJournal.create(path) as writer:
        old = writer.append(_receipt(1), genesis_witness())
        writer.append(_receipt(2), old)
    with DisconnectedReadJournal.open(path) as reader:
        with pytest.raises(ReadJournalRejected, match="tip mismatch"):
            reader.recover_receipts(old)
