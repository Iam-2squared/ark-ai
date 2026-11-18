"""Memory v1 direct-ID and persisted-event admission before private hydration.

These regression fixtures do not authenticate writers, change frozen schemas,
authorize memory disclosure or establish cross-process WAL custody.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError
import ark.memory.sqlite_store as memory_store


class ForeignString(str):
    pass


@pytest.mark.parametrize(
    "invalid_id",
    [
        ForeignString("mem_" + "a" * 64),
        "mem_" + "a" * 65,
        "mem_" + "G" * 64,
        "mem_" + "a" * 64 + "\u202e",
    ],
)
def test_direct_id_refusal_precedes_database_access(tmp_path, monkeypatch, invalid_id):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")

    def deny_open(*args, **kwargs):
        pytest.fail("invalid memory ID reached SQLite")

    monkeypatch.setattr(store, "_connect_readonly", deny_open)
    monkeypatch.setattr(store, "_connect", deny_open)
    with pytest.raises(ValueError, match="canonical deterministic memory ID"):
        store.get(invalid_id, scope, include_expired=True)
    with pytest.raises(ValueError, match="canonical deterministic memory ID"):
        store.delete(invalid_id, scope, expected_revision=1)


def test_oversized_direct_id_refused_before_regex_or_sqlite(tmp_path, monkeypatch):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")

    def no_regex(*args, **kwargs):
        pytest.fail("oversized ID reached regex engine")

    def no_sqlite(*args, **kwargs):
        pytest.fail("oversized ID reached SQLite")

    monkeypatch.setattr(memory_store, "re", type("FakeRE", (), {"fullmatch": staticmethod(no_regex)})())
    monkeypatch.setattr(store, "_connect_readonly", no_sqlite)
    monkeypatch.setattr(store, "_connect", no_sqlite)
    for action in (
        lambda: store.get("mem_" + "a" * 1_000_000, scope),
        lambda: store.delete("mem_" + "a" * 1_000_000, scope, expected_revision=1),
    ):
        with pytest.raises(ValueError, match="canonical deterministic memory ID"):
            action()


@pytest.mark.parametrize(
    ("column", "corruption"),
    [("revision", -1), ("occurred_at_ms", -1)],
)
def test_malformed_event_scalar_denied_before_event_page_hydration(
    tmp_path, monkeypatch, column, corruption,
):
    path = tmp_path / "events.sqlite3"
    scope = MemoryScope("日本語の所有者", "監査")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(MemoryWrite(scope, "合成記録", "private synthetic content"))
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE memory_id=?",
            (corruption, row.memory_id),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    real_connect = reopened._connect_readonly

    class GuardConnection:
        def __init__(self, actual):
            self.actual = actual

        def execute(self, sql, *args):
            if "SELECT * FROM memory_events" in sql:
                pytest.fail("corrupt event passed SQL-side admission")
            return self.actual.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self.actual, name)

    monkeypatch.setattr(
        reopened, "_connect_readonly", lambda: GuardConnection(real_connect()),
    )
    with pytest.raises(MemorySchemaError, match="event page hydration admission"):
        reopened.events(scope)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"SELECT {column} FROM memory_events WHERE memory_id=?",
            (row.memory_id,),
        ).fetchone() == (corruption,)
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)


def test_valid_event_revisions_and_operations_survive_preflight(tmp_path):
    path = tmp_path / "valid.sqlite3"
    scope = MemoryScope("所有者", "記録")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = store.put(MemoryWrite(scope, "出典", "元の記録"))
    store.put(MemoryWrite(scope, "出典", "更新後の記録"), expected_revision=1)
    assert store.delete(created.memory_id, scope, expected_revision=2)
    assert [
        (event.operation, event.revision, event.occurred_at_ms)
        for event in store.events(scope)
    ] == [("create", 1, 100), ("update", 2, 100), ("delete", 2, 100)]
