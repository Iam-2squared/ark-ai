"""Journal creation failure closes handles; open checks share one read epoch.

All fixtures are local synthetic SQLite receipts. Neither a SQLite snapshot
nor a hash establishes external execution, trusted custody or replay rights.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.disconnected_read_journal as module


@pytest.mark.parametrize("failed_statement", ("PRAGMA journal_mode=WAL", "COMMIT"))
def test_failed_creation_closes_connection_without_erasing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed_statement: str,
) -> None:
    path = tmp_path / "new.db"
    actual_connect = module.sqlite3.connect
    acquired: list[sqlite3.Connection] = []

    class TrackedConnection:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection
            self.closed = False

        def execute(self, statement: str, *args: object) -> object:
            if statement == failed_statement:
                raise sqlite3.OperationalError("synthetic initialization failure")
            return self.connection.execute(statement, *args)

        def close(self) -> None:
            self.closed = True
            self.connection.close()

    tracked: list[TrackedConnection] = []

    def connect(*args: object, **kwargs: object) -> TrackedConnection:
        connection = actual_connect(*args, **kwargs)
        acquired.append(connection)
        handle = TrackedConnection(connection)
        tracked.append(handle)
        return handle

    with monkeypatch.context() as patch:
        patch.setattr(module.sqlite3, "connect", connect)
        with pytest.raises(module.ReadJournalRejected, match="cannot create"):
            module.DisconnectedReadJournal.create(path)

    assert len(acquired) == len(tracked) == 1
    assert tracked[0].closed
    assert path.exists()  # failed initialization is not destructive cleanup


def test_open_schema_and_chain_scan_share_one_sqlite_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "journal.db"
    with module.DisconnectedReadJournal.create(path):
        pass
    original_scan = module.DisconnectedReadJournal._scan
    observed: list[module.ReadJournalWitness] = []
    injected = False
    row = module.ReadReceipt(
        "req_" + "a" * 32, "step_" + "1" * 16,
        "math.sum", "b" * 64, "c" * 64,
    )
    final_tip = module._chain(module._GENESIS, 1, row)

    def concurrent_scan(
        journal: module.DisconnectedReadJournal,
    ) -> module.ReadJournalWitness:
        nonlocal injected
        assert journal._connection.in_transaction
        if not injected:
            injected = True
            # Another local connection appends after the marker/schema read.
            # WAL allows the writer while the open connection pins its snapshot.
            with sqlite3.connect(path, isolation_level=None) as writer:
                writer.execute(
                    "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?)",
                    (
                        1, row.request_id, row.step_id, row.operation,
                        row.input_digest, row.result_digest,
                        module._GENESIS, final_tip,
                    ),
                )
        result = original_scan(journal)
        observed.append(result)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(module.DisconnectedReadJournal, "_scan", concurrent_scan)
        with module.DisconnectedReadJournal.open(path) as opened:
            assert opened._connection.in_transaction is False

    assert injected
    assert observed[0].count == 0
    # After releasing the snapshot, the new row is visible. The original
    # genesis witness is stale; a later caller must revalidate explicitly.
    with module.DisconnectedReadJournal.open(path) as journal:
        with pytest.raises(module.ReadJournalRejected, match="disagrees"):
            journal.verify(module.genesis_witness())
        assert journal.verify(module.ReadJournalWitness(1, final_tip)).count == 1
