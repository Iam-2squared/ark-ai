"""Memory snapshot evidence must not hide transient mutation across callbacks.

Disconnected synthetic fixtures only; no external personal-context disclosure.
"""

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "offline-memory.sqlite", clock_ms=lambda: 900)
    scope = MemoryScope("fixture-owner", "fixture-space")
    for index in range(3):
        store.put(MemoryWrite(
            scope, f"source-{index}", f"needle item {index}",
            metadata={"ordinal": index},
        ))
    request = snapshot.CoherentSnapshotRequest(
        "fixture-owner", ("fixture-space",), text="needle",
    )
    return store, request


@pytest.mark.parametrize("callback", ("hydrate", "ranking", "metadata"))
def test_transient_record_mutation_is_rejected_at_its_first_boundary(
    tmp_path, monkeypatch, callback,
):
    store, request = _fixture(tmp_path)
    original_record = snapshot._record
    original_tokens = snapshot._tokens
    original_sha256 = snapshot.hashlib.sha256
    hydrated = []
    count = 0

    def read_row(row):
        record = original_record(row)
        hydrated.append(record)
        if callback == "hydrate":
            if len(hydrated) == 2:
                object.__setattr__(hydrated[0], "content", "temporary tamper")
            elif len(hydrated) == 3:
                object.__setattr__(hydrated[0], "content", "needle item 0")
        return record

    def rank_tokens(value):
        nonlocal count
        result = original_tokens(value)
        if callback == "ranking" and value.startswith("needle item"):
            count += 1
            if count == 1:
                object.__setattr__(hydrated[0], "content", "temporary tamper")
            elif count == 2:
                object.__setattr__(hydrated[0], "content", "needle item 0")
        return result

    def hash_metadata(data=b""):
        nonlocal count
        result = original_sha256(data)
        if callback == "metadata" and data.startswith(b'{"ordinal":'):
            count += 1
            if count == 1:
                object.__setattr__(hydrated[0], "content", "temporary tamper")
            elif count == 2:
                object.__setattr__(hydrated[0], "content", "needle item 0")
        return result

    monkeypatch.setattr(snapshot, "_record", read_row)
    monkeypatch.setattr(snapshot, "_tokens", rank_tokens)
    monkeypatch.setattr(snapshot.hashlib, "sha256", hash_metadata)
    with pytest.raises(MemorySchemaError, match="snapshot record changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert len(hydrated) >= 2
    if callback != "hydrate":
        assert len(hydrated) == 3
    if callback == "metadata":
        assert count == 1


def test_stable_coherent_snapshot_retains_deterministic_content_free_witness(tmp_path):
    store, request = _fixture(tmp_path)
    before = snapshot.review_coherent_snapshot(store, request)
    after = snapshot.review_coherent_snapshot(store, request)
    assert before.provenance_sha256 == after.provenance_sha256
    assert len(before.records[0]) == 3
    assert "needle item" not in before.provenance_sha256
