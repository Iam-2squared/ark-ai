"""Memory get retains caller's exact scope carriers across callback boundaries.

Synthetic reflection tests only use temporary local Memory v1 SQLite. They
do not access personal data, grant permissions, or change frozen v1 schema.
"""

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
@pytest.mark.parametrize("boundary", ("connect", "schema", "record", "clock"))
def test_get_rejects_value_equal_scope_replacement_at_each_read_phase(
    tmp_path, monkeypatch, field, boundary,
):
    store = SQLiteMemoryStore(tmp_path / "offline-memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner-" + "z" * 80, "namespace-" + "q" * 80)
    saved = store.put(MemoryWrite(scope, "source", "synthetic-private-text"))
    original = getattr(scope, field)
    replacement = (original + "!")[:-1]
    assert replacement == original and replacement is not original
    changed = []

    def drift():
        object.__setattr__(scope, field, replacement)
        changed.append(True)

    if boundary == "connect":
        old = store._connect_readonly

        def connecting():
            conn = old()
            drift()
            return conn

        monkeypatch.setattr(store, "_connect_readonly", connecting)
    elif boundary == "schema":
        old = memory_module._validate_v1_schema

        def validating(conn):
            old(conn)
            drift()

        monkeypatch.setattr(memory_module, "_validate_v1_schema", validating)
    elif boundary == "record":
        old = memory_module._record

        def recording(row):
            result = old(row)
            drift()
            return result

        monkeypatch.setattr(memory_module, "_record", recording)
    else:
        old = store._now

        def clock():
            result = old()
            drift()
            return result

        monkeypatch.setattr(store, "_now", clock)

    with pytest.raises(MemorySchemaError, match="memory get scope changed"):
        store.get(saved.memory_id, scope)
    assert changed == [True]
    monkeypatch.undo()
    object.__setattr__(scope, field, original)
    assert store.get(saved.memory_id, scope) == saved
    assert [event.operation for event in store.events(scope)] == ["create"]


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_include_expired_get_rechecks_original_scope_without_clock(
    tmp_path, monkeypatch, field,
):
    store = SQLiteMemoryStore(tmp_path / "read.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner-" + "x" * 80, "namespace-" + "y" * 80)
    saved = store.put(MemoryWrite(scope, "source", "offline", expires_at_ms=200))
    original = getattr(scope, field)
    alias = (original + "?")[:-1]
    assert alias is not original
    old = memory_module._record

    def changed_record(row):
        record = old(row)
        object.__setattr__(scope, field, alias)
        return record

    monkeypatch.setattr(memory_module, "_record", changed_record)
    with pytest.raises(MemorySchemaError, match="memory get scope changed"):
        store.get(saved.memory_id, scope, include_expired=True)


def test_no_row_get_checks_original_scope_carriers(tmp_path, monkeypatch):
    store = SQLiteMemoryStore(tmp_path / "missing.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner-" + "p" * 80, "namespace-" + "r" * 80)
    other = MemoryScope(scope.owner_id, "another-namespace")
    saved = store.put(MemoryWrite(other, "source", "unrelated"))
    initial = scope.namespace
    replacement = (initial + "x")[:-1]
    old = store._connect_readonly

    def connecting():
        conn = old()
        object.__setattr__(scope, "namespace", replacement)
        return conn

    monkeypatch.setattr(store, "_connect_readonly", connecting)
    with pytest.raises(MemorySchemaError, match="memory get scope changed"):
        store.get(saved.memory_id, scope)
