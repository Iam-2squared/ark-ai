"""Memory single-scope readers use a coherent pre-clock SQLite snapshot."""

import pytest

from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def test_search_uses_preclock_snapshot_when_writer_commits(tmp_path):
    path = tmp_path / "memory.db"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-space")
    item = reader.put(MemoryWrite(scope, "item", "original"))
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 101)
    calls = []

    def clock():
        calls.append("read-clock")
        writer.put(MemoryWrite(scope, "item", "updated"), expected_revision=1)
        return 102

    reader._clock_ms = clock
    found = reader.search(MemoryQuery(scope, "original"))
    assert [row.content for row in found] == ["original"]
    assert calls == ["read-clock"]
    assert writer.get(item.memory_id, scope).content == "updated"


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("text", "different"),
        ("limit", 1),
        ("include_expired", True),
        ("scope", MemoryScope("other-owner", "fixture-space")),
        ("scope_namespace", "changed-namespace"),
    ],
)
def test_search_rejects_reflected_query_retargeting(tmp_path, field, replacement):
    reader = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-space")
    reader.put(MemoryWrite(scope, "item", "original"))
    query = MemoryQuery(scope, "original", limit=10)

    def clock():
        if field == "scope_namespace":
            object.__setattr__(scope, "namespace", replacement)
        else:
            object.__setattr__(query, field, replacement)
        return 102

    reader._clock_ms = clock
    with pytest.raises(MemorySchemaError, match="(scope|query) changed during clock"):
        reader.search(query)


@pytest.mark.parametrize("field", ["owner_id", "namespace"])
def test_get_rejects_reentrant_scope_retargeting(tmp_path, field):
    reader = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-space")
    item = reader.put(MemoryWrite(scope, "item", "original"))

    def clock():
        object.__setattr__(scope, field, "attacker-value")
        return 101

    reader._clock_ms = clock
    with pytest.raises(MemorySchemaError, match="get scope changed"):
        reader.get(item.memory_id, scope)


def test_get_reads_original_record_while_writer_commits_in_clock(tmp_path):
    path = tmp_path / "memory.db"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-space")
    item = reader.put(MemoryWrite(scope, "item", "original"))
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 101)

    def clock():
        writer.put(MemoryWrite(scope, "item", "updated"), expected_revision=1)
        return 102

    reader._clock_ms = clock
    assert reader.get(item.memory_id, scope).content == "original"
    assert writer.get(item.memory_id, scope).content == "updated"


def test_include_expired_get_does_not_invoke_clock(tmp_path):
    reader = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-space")
    item = reader.put(
        MemoryWrite(scope, "item", "expired", expires_at_ms=100)
    )

    def prohibited_clock():
        raise AssertionError("include_expired must not query the injected clock")

    reader._clock_ms = prohibited_clock
    assert reader.get(item.memory_id, scope, include_expired=True) == item
