"""Decoded Memory rows must survive callbacks without reflected rewrites.

Fixtures are offline and synthetic. No personal-data use or erasure is granted.
"""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as module
from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "offline-memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    written = store.put(MemoryWrite(scope, "record-1", "private apple"))
    return store, scope, written


def test_unchanged_hydrated_reads_still_return_original_records(tmp_path):
    store, scope, written = _fixture(tmp_path)
    assert store.get(written.memory_id, scope) == written
    assert store.search(MemoryQuery(scope, "apple")) == [written]
    assert store.search(MemoryQuery(scope, "not-present")) == []


@pytest.mark.parametrize("field", ("content", "revision", "scope", "metadata"))
def test_get_rejects_record_rewritten_by_clock_after_hydration(
    tmp_path, monkeypatch, field,
):
    store, scope, written = _fixture(tmp_path)
    decoded = []
    original_record = module._record

    def capture(row):
        item = original_record(row)
        decoded.append(item)
        return item

    def clock():
        if decoded:
            item = decoded[-1]
            if field == "scope":
                object.__setattr__(item.scope, "namespace", "other")
            elif field == "metadata":
                object.__setattr__(item, "metadata", {"forged": "value"})
            else:
                object.__setattr__(
                    item, field, "forged" if field == "content" else 99,
                )
        return 100

    monkeypatch.setattr(module, "_record", capture)
    store._clock_ms = clock
    with pytest.raises(MemorySchemaError, match="decoded Memory get record changed"):
        store.get(written.memory_id, scope)
    assert decoded


def test_get_rejects_record_rewritten_during_expiry_check(tmp_path, monkeypatch):
    store, scope, written = _fixture(tmp_path)
    original_expired = module._expired

    def mutate_during_expiry(item, now):
        result = original_expired(item, now)
        object.__setattr__(item, "content_sha256", "0" * 64)
        return result

    monkeypatch.setattr(module, "_expired", mutate_during_expiry)
    with pytest.raises(MemorySchemaError, match="decoded Memory get record changed"):
        store.get(written.memory_id, scope)


@pytest.mark.parametrize("field", ("content", "metadata", "scope", "revision"))
def test_search_rejects_decoded_record_rewritten_during_ranking(
    tmp_path, monkeypatch, field,
):
    store, scope, _written = _fixture(tmp_path)
    decoded = []
    original_record = module._record
    original_tokens = module._tokens

    def capture(row):
        item = original_record(row)
        decoded.append(item)
        return item

    def mutate_at_ranking(text):
        result = original_tokens(text)
        if text == "private apple" and decoded:
            item = decoded[0]
            if field == "scope":
                object.__setattr__(item.scope, "namespace", "other")
            elif field == "metadata":
                object.__setattr__(item, "metadata", {"forged": "value"})
            else:
                object.__setattr__(
                    item, field, "forged" if field == "content" else 99,
                )
        return result

    monkeypatch.setattr(module, "_record", capture)
    monkeypatch.setattr(module, "_tokens", mutate_at_ranking)
    with pytest.raises(MemorySchemaError, match="decoded Memory search record changed"):
        store.search(MemoryQuery(scope, "apple"))


@pytest.mark.parametrize("field", ("text", "limit", "include_expired"))
def test_search_rechecks_query_after_ranking_callback(tmp_path, monkeypatch, field):
    store, scope, _written = _fixture(tmp_path)
    query = MemoryQuery(scope, "apple")
    original_tokens = module._tokens

    def mutate_query(text):
        result = original_tokens(text)
        if text == "private apple":
            replacements = {
                "text": "not-apple",
                "limit": 9,
                "include_expired": True,
            }
            object.__setattr__(query, field, replacements[field])
        return result

    monkeypatch.setattr(module, "_tokens", mutate_query)
    with pytest.raises(MemorySchemaError, match="memory search query changed"):
        store.search(query)
