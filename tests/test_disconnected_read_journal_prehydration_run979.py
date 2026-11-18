"""Detached READ journal rejects damaged receipt identity before row hydration.

All operations remain digest-only; no real tool dispatch or replay is granted.
This local SQLite test does not provide independent witness/provenance.
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


@pytest.mark.parametrize(
    ("column", "corruption"),
    [
        ("seq", 0),
        ("seq", -7),
        ("operation", "other"),
        ("operation", "text.fake"),
    ],
)
def test_corrupt_read_identity_denied_before_private_row_hydration(
    tmp_path, column, corruption,
):
    path = tmp_path / "synthetic-read.sqlite3"
    original = ReadReceipt(
        "req_" + "a" * 32,
        "step_" + "b" * 16,
        "math.sum",
        "c" * 64,
        "d" * 64,
    )
    with DisconnectedReadJournal.create(path) as journal:
        retained = journal.append(original, genesis_witness())
    with sqlite3.connect(path) as connection:
        connection.execute(f"UPDATE receipts SET {column}=? WHERE seq=1", (corruption,))

    class RejectFullHydration:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, sql, *args):
            if "SELECT seq, request_id, step_id, operation" in sql:
                pytest.fail("invalid persisted identity reached row hydration")
            return self.connection.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self.connection, name)

    connection = sqlite3.connect(path, isolation_level=None)
    try:
        guarded = DisconnectedReadJournal(RejectFullHydration(connection))
        with pytest.raises(ReadJournalRejected, match="receipt hydration admission"):
            guarded._scan()
    finally:
        connection.close()

    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.open(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM receipts").fetchone() == (1,)
        assert connection.execute(
            f"SELECT {column} FROM receipts",
        ).fetchone() == (corruption,)
    assert not retained.dispatch_authorized
    assert not retained.replay_authorized


def test_valid_read_identity_survives_cold_restart_and_remains_inert(tmp_path):
    path = tmp_path / "valid-read.sqlite3"
    with DisconnectedReadJournal.create(path) as journal:
        tip = genesis_witness()
        for number, op in enumerate(
            ("math.sum", "text.stats", "text.find", "json.inspect"), 1,
        ):
            tip = journal.append(
                ReadReceipt(
                    "req_" + f"{number:032x}",
                    "step_" + f"{number:016x}",
                    op, "a" * 64, "b" * 64,
                ),
                tip,
            )
    with DisconnectedReadJournal.open(path) as reopened:
        assert reopened.verify(tip) == tip
        assert tip.count == 4
        assert not tip.dispatch_authorized
        assert not tip.effect_proven
        assert not tip.replay_authorized
        assert not tip.independent_custody_proven
