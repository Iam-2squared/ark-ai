"""A disposable occurrence schema oracle closes on every comparison outcome.

The tests use only in-memory synthetic SQLite data; a valid reservation
schema does not grant dispatch authority or authenticate an issuer.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.durable_occurrence_review as occurrence


def _fixture(ddl: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl)
    conn.execute("PRAGMA user_version=1")
    return conn


def _track_oracle(monkeypatch):
    opened: list[sqlite3.Connection] = []
    closed: list[sqlite3.Connection] = []
    connect_original = sqlite3.connect

    class Oracle(sqlite3.Connection):
        def close(self):
            closed.append(self)
            return super().close()

    def connect(database, *args, **kwargs):
        if database == ":memory:":
            assert "factory" not in kwargs
            created = connect_original(
                database, *args, factory=Oracle, **kwargs,
            )
            opened.append(created)
            return created
        return connect_original(database, *args, **kwargs)

    monkeypatch.setattr(occurrence.sqlite3, "connect", connect)
    return opened, closed


def _assert_closed(opened, closed) -> None:
    assert len(opened) == len(closed) == 1
    assert opened[0] is closed[0]


def test_occurrence_schema_oracle_closes_on_valid_schema(monkeypatch) -> None:
    with closing(_fixture(occurrence._TABLE)) as conn:
        opened, closed = _track_oracle(monkeypatch)
        occurrence._validate(conn)
        _assert_closed(opened, closed)


def test_occurrence_oracle_closes_on_same_count_foreign_schema(
    monkeypatch,
) -> None:
    foreign = occurrence._TABLE.replace(
        "reserved_at_ms INTEGER NOT NULL", "reserved_at_ms TEXT NOT NULL",
    )
    with closing(_fixture(foreign)) as conn:
        opened, closed = _track_oracle(monkeypatch)
        with pytest.raises(
            occurrence.SyntheticReplayRejected, match="schema changed",
        ):
            occurrence._validate(conn)
        _assert_closed(opened, closed)


def test_occurrence_oracle_closes_if_catalog_reader_raises(
    monkeypatch,
) -> None:
    with closing(_fixture(occurrence._TABLE)) as conn:
        opened, closed = _track_oracle(monkeypatch)

        def fail_catalog(_conn):
            raise RuntimeError("synthetic catalog read fault")

        monkeypatch.setattr(occurrence, "_objects", fail_catalog)
        with pytest.raises(RuntimeError, match="synthetic catalog read fault"):
            occurrence._validate(conn)
        _assert_closed(opened, closed)
