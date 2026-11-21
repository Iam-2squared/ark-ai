"""READ-journal cold open must not recreate an absent file after path admission."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadReceipt,
    genesis_witness,
)


def test_missing_file_after_preflight_is_not_recreated(tmp_path, monkeypatch) -> None:
    path = tmp_path / "synthetic-read.sqlite3"
    with DisconnectedReadJournal.create(path):
        pass
    native_connect = sqlite3.connect
    visited = []

    def remove_before_native_open(target, *args, **kwargs):
        visited.append((target, kwargs.get("uri")))
        if target == path.as_uri() + "?mode=rw":
            path.unlink()
        return native_connect(target, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", remove_before_native_open)
        with pytest.raises(ReadJournalRejected, match="unreadable journal schema"):
            DisconnectedReadJournal.open(path)
    assert visited == [(path.as_uri() + "?mode=rw", True)]
    assert not path.exists()
    assert not path.with_name(path.name + "-journal").exists()


def test_existing_journal_reopens_without_creating_and_keeps_witness(tmp_path) -> None:
    path = tmp_path / "synthetic-read.sqlite3"
    row = ReadReceipt(
        "req_" + "a" * 32, "step_" + "b" * 16,
        "math.sum", "c" * 64, "d" * 64,
    )
    with DisconnectedReadJournal.create(path) as journal:
        retained = journal.append(row, genesis_witness())

    with DisconnectedReadJournal.open(path) as reopened:
        observed = reopened.verify(retained)
        assert observed == retained
        assert observed.dispatch_authorized is False
        assert observed.effect_proven is False
        assert observed.replay_authorized is False
    assert path.is_file()
