"""Synthetic v1 Memory bootstrap must be atomic, without migration or repair."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_store as memory_module


def test_fresh_bootstrap_is_version_one_and_preserves_basic_use(tmp_path):
    path = tmp_path / "fresh.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 123)
    scope = MemoryScope("fixture-owner")
    item = store.put(MemoryWrite(scope, "source", "content"))
    assert store.get(item.memory_id, scope) == item
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1


@pytest.mark.parametrize("statement", [
    "CREATE TABLE alien(value TEXT)",
    "CREATE INDEX alien_index ON alien(value)",
])
def test_occupied_version_zero_is_never_repaired(tmp_path, statement):
    path = tmp_path / "occupied.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE alien(value TEXT)")
        if statement.startswith("CREATE INDEX"):
            conn.execute(statement)
        conn.execute("PRAGMA user_version=0")
    with pytest.raises(MemorySchemaError, match="not empty"):
        SQLiteMemoryStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='memories'"
        ).fetchone() is None
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='alien'"
        ).fetchone() is not None


def test_negative_version_rejected_without_schema_mutation(tmp_path):
    path = tmp_path / "negative.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=-1")
    with pytest.raises(MemorySchemaError, match="negative"):
        SQLiteMemoryStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == -1
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='memories'"
        ).fetchone() is None


def test_failed_post_ddl_validation_rolls_back_all_bootstrap_objects(
    tmp_path, monkeypatch
):
    path = tmp_path / "rollback.sqlite3"

    def reject(_conn):
        raise MemorySchemaError("synthetic post-DDL fault")

    with monkeypatch.context() as patch:
        patch.setattr(memory_module, "_validate_v1_schema", reject)
        with pytest.raises(MemorySchemaError, match="synthetic post-DDL"):
            SQLiteMemoryStore(path)

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        names = conn.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        assert names == []
    SQLiteMemoryStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1


def test_two_initializers_converge_on_one_valid_v1_schema(tmp_path):
    path = tmp_path / "concurrent.sqlite3"

    def open_store(_n):
        SQLiteMemoryStore(path, clock_ms=lambda: 10)
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(open_store, range(2))) == [True, True]
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name='memories'").fetchone()[0] == 1
