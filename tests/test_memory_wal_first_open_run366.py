"""WAL negotiation belongs to bootstrap, never routine read connections."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def test_reader_opens_while_another_connection_holds_writer_slot(tmp_path):
    path = tmp_path / "memory.db"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    item = store.put(MemoryWrite(scope, "item", "safe"))
    with sqlite3.connect(path) as writer:
        assert writer.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        writer.execute("BEGIN IMMEDIATE")
        assert store.get(item.memory_id, scope, include_expired=True) == item
        assert store.search(store_query(scope))[0] == item
        writer.rollback()


def store_query(scope):
    from ark.memory import MemoryQuery

    return MemoryQuery(scope, include_expired=True)


def test_repeated_two_initializer_races_leave_one_valid_v1_schema(tmp_path):
    for i in range(4):
        path = tmp_path / f"initializers-{i}.db"

        def open_store(_index, db_path=path):
            return SQLiteMemoryStore(db_path, clock_ms=lambda: 100)

        with ThreadPoolExecutor(max_workers=2) as pool:
            opened = list(pool.map(open_store, range(2)))
        assert len(opened) == 2
        with sqlite3.connect(path) as conn:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name='memories'"
            ).fetchone()[0] == 1
