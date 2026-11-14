"""Coherent Memory snapshots reject an equal-valued namespace carrier swap.

These are local SQLite fixture reviews, not consent or privacy disclosure.
"""

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 900)
    scope = MemoryScope("offline-owner", "offline-namespace")
    store.put(MemoryWrite(
        scope, "source", "needle text", metadata={"ordinal": "1"},
    ))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), text="needle",
    )
    return store, request


def test_stable_namespace_carrier_produces_inert_snapshot(tmp_path):
    store, request = _fixture(tmp_path)
    first = snapshot.review_coherent_snapshot(store, request)
    second = snapshot.review_coherent_snapshot(store, request)
    assert first.provenance_sha256 == second.provenance_sha256
    assert len(first.records[0]) == 1


@pytest.mark.parametrize("phase", ("query", "row", "metadata"))
def test_equal_valued_namespace_tuple_replacement_is_rejected(
    tmp_path, monkeypatch, phase,
):
    store, request = _fixture(tmp_path)
    original_namespaces = request.namespaces

    def replace_carrier():
        new_namespaces = tuple(list(original_namespaces))
        assert new_namespaces == original_namespaces
        assert new_namespaces is not original_namespaces
        object.__setattr__(request, "namespaces", new_namespaces)

    if phase == "query":
        original_tokens = snapshot._tokens

        def tokens(value):
            result = original_tokens(value)
            if value == "needle":
                replace_carrier()
            return result

        monkeypatch.setattr(snapshot, "_tokens", tokens)
    elif phase == "row":
        original_record = snapshot._record

        def record(row):
            value = original_record(row)
            replace_carrier()
            return value

        monkeypatch.setattr(snapshot, "_record", record)
    else:
        original_sha256 = snapshot.hashlib.sha256

        def sha256(data=b""):
            digest = original_sha256(data)
            if data.startswith(b'{"ordinal":'):
                replace_carrier()
            return digest

        monkeypatch.setattr(snapshot.hashlib, "sha256", sha256)

    with pytest.raises(MemorySchemaError, match="snapshot request changed"):
        snapshot.review_coherent_snapshot(store, request)
