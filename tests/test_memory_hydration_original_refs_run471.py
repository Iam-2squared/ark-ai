"""Hydrated Memory read epochs keep nested originals alive against id reuse.

No actual personal context is used; the frozen Memory v1 schema and public
store API are unchanged.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from ark.memory.contracts import MemoryRecord, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore, _hydrated_record_epoch


def _record():
    return MemoryRecord(
        "m_" + "a" * 64, MemoryScope("owner", "synthetic"),
        "source", "fixture", {"safe": "yes"},
        100, 100, None, 1, "a" * 64,
    )


def test_hydrated_epoch_holds_exact_original_nested_carriers():
    record = _record()
    original_scope = record.scope
    original_metadata = record.metadata
    epoch = _hydrated_record_epoch(record)
    assert epoch[-2] is original_scope
    assert epoch[-1] is original_metadata
    assert type(epoch[-1]) is MappingProxyType


@pytest.mark.parametrize("field", ("scope", "metadata"))
def test_equal_value_nested_carrier_substitution_changes_epoch(field):
    record = _record()
    original = getattr(record, field)
    epoch = _hydrated_record_epoch(record)
    if field == "scope":
        replacement = MemoryScope(original.owner_id, original.namespace)
    else:
        replacement = MappingProxyType(dict(original))
    assert replacement == original and replacement is not original
    object.__setattr__(record, field, replacement)
    assert epoch[-2 if field == "scope" else -1] is original
    assert _hydrated_record_epoch(record) != epoch


def test_normal_sqlite_read_and_search_remain_valid(tmp_path):
    clock = lambda: 101
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=clock)
    scope = MemoryScope("owner", "synthetic")
    created = store.put(MemoryWrite(scope, "source", "fixture"))
    found = store.get(created.memory_id, scope)
    assert found is not None and found.revision == 1
    from ark.memory.contracts import MemoryQuery

    matches = store.search(MemoryQuery(scope, text="fixture"))
    assert len(matches) == 1 and matches[0].memory_id == created.memory_id
