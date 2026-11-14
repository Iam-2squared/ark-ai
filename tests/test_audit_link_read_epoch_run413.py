"""Sidecar read-only witness cannot use swapped sources/retained carriers.

All SQL databases are disconnected fixtures. The reviewer never authorizes
notification, physical effects, external WRITE outcomes or automatic replay.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.agency.synthetic_occurrence_audit_link_review as links
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
)


def _fixture(tmp_path):
    path = tmp_path / "links.sqlite"
    store = SyntheticOccurrenceAuditLinkStore(path)
    retained = store.read_witness()
    return store, path, retained


def _equal_string_copy(value):
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


def test_unchanged_retained_link_witness_still_passes(tmp_path):
    store, _path, retained = _fixture(tmp_path)
    current = store.read_witness(retained=retained)
    assert current == retained
    assert current.event_count == 0


def test_sqlite_open_source_replacement_is_rejected(tmp_path, monkeypatch):
    store, path, retained = _fixture(tmp_path)
    opened = []
    original = store._connect

    def open_and_swap(*, create=False, readonly=False):
        conn = original(create=create, readonly=readonly)
        if readonly:
            opened.append(conn)
            store._path = Path(str(path))
        return conn

    monkeypatch.setattr(store, "_connect", open_and_swap)
    with pytest.raises(SyntheticAuditLinkRejected, match="source or retained"):
        store.read_witness(retained=retained)
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")


def test_begin_callback_source_replacement_fails_before_replay(
    tmp_path, monkeypatch,
):
    store, path, retained = _fixture(tmp_path)
    actual = store._connect
    replay_called = []
    saved_replay = links._replay

    def replay(conn):
        replay_called.append(True)
        return saved_replay(conn)

    class ConnectionProxy:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, sql, *args):
            result = self.conn.execute(sql, *args)
            if sql == "BEGIN":
                store._path = Path(str(path))
            return result

        def __getattr__(self, name):
            return getattr(self.conn, name)

    def opening(*, readonly=False, create=False):
        return ConnectionProxy(actual(readonly=readonly, create=create))

    monkeypatch.setattr(store, "_connect", opening)
    monkeypatch.setattr(links, "_replay", replay)
    with pytest.raises(SyntheticAuditLinkRejected, match="source or retained"):
        store.read_witness(retained=retained)
    assert replay_called == []


@pytest.mark.parametrize("boundary", ["shape", "replay"])
def test_equal_valued_retained_carrier_replacement_fails(
    tmp_path, monkeypatch, boundary,
):
    store, _path, retained = _fixture(tmp_path)
    if boundary == "shape":
        original_shape = links.SyntheticAuditLinkWitness.assert_shape

        def swapped_shape(self):
            original_shape(self)
            if self is retained:
                object.__setattr__(
                    retained, "tail_hash", _equal_string_copy(retained.tail_hash),
                )

        monkeypatch.setattr(
            links.SyntheticAuditLinkWitness, "assert_shape", swapped_shape,
        )
    else:
        original_replay = links._replay

        def replay(conn):
            result = original_replay(conn)
            object.__setattr__(
                retained, "tail_hash", _equal_string_copy(retained.tail_hash),
            )
            return result

        monkeypatch.setattr(links, "_replay", replay)
    with pytest.raises(SyntheticAuditLinkRejected, match="source or retained"):
        store.read_witness(retained=retained)
