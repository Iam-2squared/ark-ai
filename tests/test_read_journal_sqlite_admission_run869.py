"""Disconnected READ journal SQLite markers/receipts and native path admission.

Only fabricated digests are stored; no READ ToolBackend, consent, or external effect.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadReceipt,
    genesis_witness,
)


def _seed(tmp_path):
    path = tmp_path / "read_journal.sqlite"
    with DisconnectedReadJournal.create(path) as journal:
        first = journal.append(
            ReadReceipt(
                "req_" + "a" * 32, "step_" + "1" * 16, "math.sum",
                "b" * 64, "c" * 64,
            ),
            genesis_witness(),
        )
    return path, first


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("request_id", "é" * 36),
        ("step_id", "é" * 21),
        ("operation", "é" * 32),
        ("input_digest", "é" * 64),
        ("result_digest", sqlite3.Binary(b"d" * 64)),
        ("previous_sha", "é" * 64),
        ("chain_sha", "é" * 64),
    ),
)
def test_foreign_read_receipt_rejected_before_hydration(tmp_path, column, replacement):
    path, _ = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE receipts SET {column}=? WHERE seq=1", (replacement,),
        ).rowcount == 1
    with pytest.raises(ReadJournalRejected, match="hydration admission"):
        DisconnectedReadJournal.open(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM receipts").fetchone() == (1,)


@pytest.mark.parametrize("replacement", ("é" * 28, sqlite3.Binary(b"x" * 28)))
def test_marker_refuses_oversized_or_blob_value_before_python_read(tmp_path, replacement):
    path, _ = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE marker SET revision=?", (replacement,))
    with pytest.raises(ReadJournalRejected, match="marker hydration admission"):
        DisconnectedReadJournal.open(path)


@pytest.mark.parametrize("name", ("bad\x00name.sqlite", "é" * 2100))
def test_native_journal_path_rejected_before_io(tmp_path, name):
    path = tmp_path / name
    with pytest.raises(ReadJournalRejected, match="path|Path"):
        DisconnectedReadJournal.create(path)


def test_ascii_receipts_still_recover_without_replay_authority(tmp_path):
    path, first = _seed(tmp_path)
    with DisconnectedReadJournal.open(path) as journal:
        snapshot = journal.recover_receipts(first)
        assert snapshot.witness == first
        assert len(snapshot.receipts) == 1
        assert snapshot.automatic_replay_authorized is False
        assert snapshot.dispatch_authorized is False
        assert snapshot.independent_custody_proven is False
