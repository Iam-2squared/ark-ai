"""Synthetic READ journal recovery remains coherent across WAL commits.

Both tests operate on disposable local SQLite handles. A digest-only recovery
snapshot proves neither independent custody nor execution, replay or dispatch.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.disconnected_read_journal as journal


def _receipt(index: int) -> journal.ReadReceipt:
    return journal.ReadReceipt(
        "req_" + "a" * 32, "step_" + f"{index:016x}", "math.sum",
        "b" * 64, "c" * 64,
    )


def test_recovery_snapshot_ignores_concurrent_append_until_new_read(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "recovery-wal-append.sqlite"
    with journal.DisconnectedReadJournal.create(path) as seed:
        retained = seed.append(_receipt(1), journal.genesis_witness())

    with journal.DisconnectedReadJournal.open(path) as reader:
        with journal.DisconnectedReadJournal.open(path) as writer:
            original = journal.DisconnectedReadJournal._scan
            advanced = []
            scans = []

            def concurrent_scan(instance):
                observed = original(instance)
                if instance is reader:
                    assert reader._connection.in_transaction
                    scans.append(observed)
                    if not advanced:
                        # Writer commits after the reader's first BEGIN/snapshot.
                        advanced.append(writer.append(_receipt(2), retained))
                return observed

            with monkeypatch.context() as patch:
                patch.setattr(journal.DisconnectedReadJournal, "_scan", concurrent_scan)
                recovered = reader.recover_receipts(retained)

            assert recovered.witness == retained
            assert recovered.receipts == (_receipt(1),)
            assert all(value == retained for value in scans)
            assert advanced[0].count == 2
            assert recovered.dispatch_authorized is False
            assert recovered.automatic_replay_authorized is False
            # A NEW snapshot must not mistake the earlier valid snapshot for
            # the current tip or grant an automatic retry.
            with pytest.raises(journal.ReadJournalRejected, match="external witness"):
                reader.verify(retained)
            assert writer.verify(advanced[0]) == advanced[0]


def test_recovery_snapshot_does_not_rebase_deleted_tail(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "recovery-wal-tail.sqlite"
    with journal.DisconnectedReadJournal.create(path) as seed:
        first = seed.append(_receipt(1), journal.genesis_witness())
        retained = seed.append(_receipt(2), first)

    with journal.DisconnectedReadJournal.open(path) as reader:
        original = journal.DisconnectedReadJournal._scan
        injected = []
        scans = []

        def concurrent_scan(instance):
            observed = original(instance)
            scans.append(observed)
            if instance is reader and not injected:
                injected.append(True)
                with closing(sqlite3.connect(path)) as writer:
                    with writer:
                        writer.execute("DELETE FROM receipts WHERE seq=2")
            return observed

        with monkeypatch.context() as patch:
            patch.setattr(journal.DisconnectedReadJournal, "_scan", concurrent_scan)
            recovered = reader.recover_receipts(retained)

        assert injected == [True]
        assert recovered.receipts == (_receipt(1), _receipt(2))
        assert recovered.witness == retained
        assert all(value == retained for value in scans)
        assert recovered.effect_proven is False
        assert recovered.independent_custody_proven is False

    # A later review must explicitly discover the truncated current tip; an
    # earlier consistent read-only snapshot cannot authenticate persistence.
    with journal.DisconnectedReadJournal.open(path) as later:
        with pytest.raises(journal.ReadJournalRejected, match="external witness"):
            later.verify(retained)
        assert later.verify(first) == first
