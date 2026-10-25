"""Detached Memory snapshots must survive the final result-constructor boundary.

Local disposable SQLite fixtures only; no real personal-data access, erasure or
external actions. The Memory v1 schema and frozen evidence remain unchanged.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    for index in range(2):
        store.put(MemoryWrite(
            scope, f"fixture-source-{index}", f"needle {index}",
            metadata={"ordinal": str(index)},
        ))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), text="needle",
    )
    return store, request


@pytest.mark.parametrize("target", ("request", "source", "record"))
def test_result_constructor_cannot_retarget_original_snapshot(
    tmp_path, monkeypatch, target,
):
    store, request = _fixture(tmp_path)
    native_result = snapshot.CoherentSnapshotReview
    original_record = snapshot._record
    hydrated = []

    def hydrate(row):
        value = original_record(row)
        hydrated.append(value)
        return value

    def construct(*args):
        value = native_result(*args)
        if target == "request":
            object.__setattr__(request, "text", "retargeted")
        elif target == "source":
            earlier = store.path
            store.path = Path(str(earlier))
            assert store.path == earlier
            assert store.path is not earlier
        else:
            assert hydrated
            object.__setattr__(hydrated[0], "source_id", "retargeted")
        return value

    monkeypatch.setattr(snapshot, "_record", hydrate)
    monkeypatch.setattr(snapshot, "CoherentSnapshotReview", construct)
    with pytest.raises(MemorySchemaError, match={
        "request": "snapshot request changed",
        "source": "memory snapshot source path changed",
        "record": "memory snapshot record changed",
    }[target]):
        snapshot.review_coherent_snapshot(store, request)


@pytest.mark.parametrize(
    "target",
    ("type", "read_at_ms", "scopes", "records", "provenance_sha256"),
)
def test_result_constructor_cannot_forge_detached_witness(
    tmp_path, monkeypatch, target,
):
    store, request = _fixture(tmp_path)
    native_result = snapshot.CoherentSnapshotReview

    def construct(*args):
        if target == "type":
            return object()
        value = native_result(*args)
        if target == "read_at_ms":
            replacement = int(str(value.read_at_ms))
            assert replacement == value.read_at_ms
            assert replacement is not value.read_at_ms
            object.__setattr__(value, "read_at_ms", replacement)
        elif target == "scopes":
            replacement = tuple(list(value.scopes))
            assert replacement == value.scopes
            assert replacement is not value.scopes
            object.__setattr__(value, "scopes", replacement)
        elif target == "records":
            replacement = tuple(list(value.records))
            assert replacement == value.records
            assert replacement is not value.records
            object.__setattr__(value, "records", replacement)
        else:
            replacement = ("x" + value.provenance_sha256)[1:]
            assert replacement == value.provenance_sha256
            assert replacement is not value.provenance_sha256
            object.__setattr__(value, "provenance_sha256", replacement)
        return value

    monkeypatch.setattr(snapshot, "CoherentSnapshotReview", construct)
    with pytest.raises(MemorySchemaError, match="memory snapshot result changed"):
        snapshot.review_coherent_snapshot(store, request)


def test_stable_snapshot_result_keeps_deterministic_witness(tmp_path):
    store, request = _fixture(tmp_path)
    first = snapshot.review_coherent_snapshot(store, request)
    second = snapshot.review_coherent_snapshot(store, request)
    assert first == second
    assert len(first.records[0]) == 2
    assert len(first.provenance_sha256) == 64
