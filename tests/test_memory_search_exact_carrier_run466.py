"""Memory search must reject reflected same-valued input replacements.

Synthetic fault injection uses only temporary SQLite fixtures. No private data,
frozen schema changes, consent assertions, or external Tool execution.
"""

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory import MemoryQuery, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize("field", ("owner_id", "namespace", "text"))
@pytest.mark.parametrize("boundary", ("connect", "schema", "record", "clock"))
def test_search_rejects_value_equal_new_string_carrier(
    tmp_path, monkeypatch, field, boundary,
):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 500)
    scope = MemoryScope("owner-" + "x" * 80, "namespace-" + "y" * 80)
    store.put(MemoryWrite(scope, "synthetic", "alpha " + "z" * 80))
    query = MemoryQuery(scope, "alpha " + "z" * 80)
    target = query if field == "text" else scope
    original = getattr(target, field)
    replacement = (original + "!")[:-1]
    assert replacement == original and replacement is not original
    changed = []

    def drift():
        object.__setattr__(target, field, replacement)
        changed.append(True)

    if boundary == "connect":
        old = store._connect_readonly

        def connect():
            connection = old()
            drift()
            return connection

        monkeypatch.setattr(store, "_connect_readonly", connect)
    elif boundary == "schema":
        old = memory_module._validate_v1_schema

        def validate(connection):
            old(connection)
            drift()

        monkeypatch.setattr(memory_module, "_validate_v1_schema", validate)
    elif boundary == "record":
        old = memory_module._record

        def hydrate(row):
            result = old(row)
            drift()
            return result

        monkeypatch.setattr(memory_module, "_record", hydrate)
    else:
        old = store._now

        def clock():
            value = old()
            drift()
            return value

        monkeypatch.setattr(store, "_now", clock)

    match = "memory search query changed" if field == "text" else "memory search scope changed"
    with pytest.raises(MemorySchemaError, match=match):
        store.search(query)
    assert changed == [True]
    monkeypatch.undo()
    object.__setattr__(target, field, original)
    assert len(store.search(query)) == 1
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_normal_original_carriers_search_across_expiry(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "stable.sqlite", clock_ms=lambda: 500)
    scope = MemoryScope("owner-" + "x" * 80, "namespace-" + "y" * 80)
    store.put(MemoryWrite(scope, "note", "alpha", expires_at_ms=501))
    q = MemoryQuery(scope, "alpha")
    assert len(store.search(q)) == 1
    q_expired = MemoryQuery(scope, "alpha", include_expired=True)
    assert len(store.search(q_expired)) == 1


def test_search_refuses_transient_equal_text_swap_at_schema_edge(tmp_path, monkeypatch):
    store = SQLiteMemoryStore(tmp_path / "transient.sqlite", clock_ms=lambda: 500)
    scope = MemoryScope("long-owner-" + "x" * 90)
    store.put(MemoryWrite(scope, "note", "alpha"))
    query = MemoryQuery(scope, "alpha-" + "y" * 90)
    original = query.text
    equal_new = (original + "?")[:-1]
    assert equal_new == original and equal_new is not original
    old = memory_module._validate_v1_schema

    def transient(conn):
        old(conn)
        object.__setattr__(query, "text", equal_new)

    monkeypatch.setattr(memory_module, "_validate_v1_schema", transient)
    with pytest.raises(MemorySchemaError, match="memory search query changed"):
        store.search(query)
