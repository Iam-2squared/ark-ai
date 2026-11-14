"""Detached READ journal rejects authority spoofing before durable writes.

These regressions operate on local synthetic SQLite fixtures only. A retained
witness is a history comparator, never a permission to dispatch or replay.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.disconnected_read_journal as module

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16
_DIGEST = "b" * 64
_FLAGS = (
    "dispatch_authorized",
    "effect_proven",
    "replay_authorized",
    "independent_custody_proven",
)


def _receipt() -> module.ReadReceipt:
    return module.ReadReceipt(_REQUEST, _STEP, "math.sum", _DIGEST, "c" * 64)


@pytest.mark.parametrize("flag", _FLAGS)
def test_append_forged_retained_authority_does_not_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flag: str,
) -> None:
    with module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        witness = module.genesis_witness()
        with monkeypatch.context() as patch:
            patch.setattr(module.ReadJournalWitness, flag, property(lambda self: True))
            with pytest.raises(module.ReadJournalRejected, match="invalid retained witness"):
                journal.append(_receipt(), witness)
        assert journal.verify(module.genesis_witness()).count == 0


@pytest.mark.parametrize("flag", _FLAGS)
def test_verify_forged_retained_authority_cannot_be_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flag: str,
) -> None:
    with module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        with monkeypatch.context() as patch:
            patch.setattr(module.ReadJournalWitness, flag, property(lambda self: True))
            with pytest.raises(module.ReadJournalRejected, match="invalid retained witness"):
                journal.verify(module.genesis_witness())
        assert journal.verify(module.genesis_witness()).count == 0


def test_forged_authority_during_hash_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        retained = module.genesis_witness()
        real_chain = module._chain
        with monkeypatch.context() as patch:

            def poison(previous: str, index: int, row: module.ReadReceipt) -> str:
                result = real_chain(previous, index, row)
                patch.setattr(
                    module.ReadJournalWitness, "replay_authorized",
                    property(lambda self: True),
                )
                return result

            patch.setattr(module, "_chain", poison)
            with pytest.raises(module.ReadJournalRejected, match="invalid retained witness"):
                journal.append(_receipt(), retained)
        assert journal.verify(module.genesis_witness()).count == 0


@pytest.mark.parametrize("failure", ("foreign_marker", "sqlite_error"))
def test_rejected_open_closes_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    path = tmp_path / "existing.db"
    path.write_bytes(b"non-sensitive fake database fixture")

    class FakeConnection:
        def __init__(self) -> None:
            self.closed = False

        def execute(self, statement: str, *args: object) -> SimpleNamespace:
            if failure == "sqlite_error":
                raise sqlite3.OperationalError("synthetic failed PRAGMA")
            if statement == "SELECT revision FROM marker":
                return SimpleNamespace(fetchmany=lambda size: [("foreign",)][:size])
            return SimpleNamespace(fetchall=lambda: [])

        def close(self) -> None:
            self.closed = True

    fake = FakeConnection()
    with monkeypatch.context() as patch:
        patch.setattr(module.sqlite3, "connect", lambda *args, **kwargs: fake)
        with pytest.raises(
            module.ReadJournalRejected,
            match="foreign journal marker|unreadable journal schema",
        ):
            module.DisconnectedReadJournal.open(path)
    assert fake.closed
