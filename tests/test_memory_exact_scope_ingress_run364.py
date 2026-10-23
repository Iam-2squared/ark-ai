"""Synthetic Memory v1 scope ingress rejects duck typing and clock reflection."""

import pytest

from ark.memory.contracts import (
    MemoryEvent,
    MemoryQuery,
    MemoryRecord,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
)
from ark.memory.sqlite_store import SQLiteMemoryStore, deterministic_memory_id


class ImitationScope:
    owner_id = "fixture-owner"
    namespace = "fixture-space"


class SubclassScope(MemoryScope):
    pass


@pytest.mark.parametrize(
    "constructor",
    (
        lambda scope: MemoryWrite(scope, "source", "fixture"),
        lambda scope: MemoryQuery(scope),
        lambda scope: MemoryRecord("mem_" + "0" * 64, scope, "source", "fixture", {}, 1, 1, None, 1, "0" * 64),
        lambda scope: MemoryEvent(1, "mem_" + "0" * 64, scope, "create", 1, 1),
    ),
)
@pytest.mark.parametrize("scope", (ImitationScope(), SubclassScope("fixture-owner", "fixture-space")))
def test_public_values_require_exact_scope_type(constructor, scope):
    with pytest.raises(TypeError, match="exact MemoryScope"):
        constructor(scope)


@pytest.mark.parametrize("api", ("identity", "get", "events", "delete", "purge"))
def test_store_ingress_rejects_imitation_scope_without_side_effect(tmp_path, api):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    valid = MemoryScope("fixture-owner", "fixture-space")
    record = store.put(MemoryWrite(valid, "source", "fixture"))
    fake = ImitationScope()
    with pytest.raises(TypeError, match="exact MemoryScope"):
        if api == "identity":
            deterministic_memory_id(fake, "source")
        elif api == "get":
            store.get(record.memory_id, fake, include_expired=True)
        elif api == "events":
            store.events(fake)
        elif api == "delete":
            store.delete(record.memory_id, fake, expected_revision=1)
        else:
            store.purge_expired(scope=fake)
    assert store.get(record.memory_id, valid, include_expired=True).content == "fixture"
    assert len(store.events(valid)) == 1


def test_reflected_put_scope_type_rejected_before_clock(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    write = MemoryWrite(MemoryScope("fixture-owner"), "source", "fixture")
    object.__setattr__(write, "scope", ImitationScope())
    with pytest.raises(TypeError, match="exact MemoryWrite"):
        store.put(write)


def test_reflected_search_scope_type_rejected_before_clock(tmp_path):
    calls = []
    def clock():
        calls.append(1)
        return 100

    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=clock)
    query = MemoryQuery(MemoryScope("fixture-owner"))
    object.__setattr__(query, "scope", ImitationScope())
    with pytest.raises(TypeError, match="exact MemoryQuery"):
        store.search(query)
    assert calls == []


def test_clock_cannot_retarget_an_existing_search_query(tmp_path):
    original = MemoryScope("fixture-owner", "fixture-space")
    other = MemoryScope("another-owner", "fixture-space")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    store.put(MemoryWrite(original, "source", "fixture"))
    store.put(MemoryWrite(other, "source", "other"))
    query = MemoryQuery(original)

    def retargeting_clock():
        object.__setattr__(query, "scope", other)
        return 101

    store._clock_ms = retargeting_clock
    with pytest.raises(MemorySchemaError, match="scope changed during clock"):
        store.search(query)
