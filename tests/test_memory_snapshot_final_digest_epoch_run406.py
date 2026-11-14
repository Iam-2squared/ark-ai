"""Final content-free Memory witness must stay bound across digest callbacks.

Disposable SQLite only; no schema mutation, export, erasure or real tools.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1100)
    scope = MemoryScope("offline-owner", "offline-space")
    store.put(MemoryWrite(scope, "synthetic-source", "fixture text"))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), text="fixture",
    )
    return store, request


@pytest.mark.parametrize("phase", ("serialize", "hash"))
@pytest.mark.parametrize("target", ("request", "source", "record"))
def test_final_digest_callbacks_must_not_retarget_prior_snapshot(
    tmp_path, monkeypatch, phase, target,
):
    store, request = _fixture(tmp_path)
    hydrated = []
    original_record = snapshot._record
    original_dumps = snapshot.json.dumps
    original_sha256 = snapshot.hashlib.sha256

    def hydrate(row):
        record = original_record(row)
        hydrated.append(record)
        return record

    def mutate():
        if target == "request":
            object.__setattr__(request, "text", "retargeted")
        elif target == "source":
            original_path = store.path
            store.path = Path(str(original_path))
            assert store.path == original_path
            assert store.path is not original_path
        else:
            assert hydrated
            object.__setattr__(hydrated[0], "source_id", "retargeted")

    def serialize(payload, **kwargs):
        encoded = original_dumps(payload, **kwargs)
        if (
            phase == "serialize"
            and isinstance(payload, dict)
            and payload.get("witness_format_version") == 2
        ):
            mutate()
        return encoded

    def sha256(payload=b"", *args, **kwargs):
        digest = original_sha256(payload, *args, **kwargs)
        if phase == "hash" and b'"witness_format_version":2' in payload:
            mutate()
        return digest

    monkeypatch.setattr(snapshot, "_record", hydrate)
    monkeypatch.setattr(snapshot.json, "dumps", serialize)
    monkeypatch.setattr(snapshot.hashlib, "sha256", sha256)
    with pytest.raises(MemorySchemaError, match={
        "request": "request changed",
        "source": "source path changed",
        "record": "record changed",
    }[target]):
        snapshot.review_coherent_snapshot(store, request)
    assert len(hydrated) == 1


def test_serialization_drift_must_be_seen_before_hash_callback_restores_it(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    original_dumps = snapshot.json.dumps
    original_sha256 = snapshot.hashlib.sha256
    observed = []

    def serialize(payload, **kwargs):
        encoded = original_dumps(payload, **kwargs)
        if isinstance(payload, dict) and payload.get("witness_format_version") == 2:
            object.__setattr__(request, "text", "temporary-retarget")
            observed.append("retarget")
        return encoded

    def sha256(payload=b"", *args, **kwargs):
        if b'"witness_format_version":2' in payload:
            object.__setattr__(request, "text", "fixture")
            observed.append("restore")
        return original_sha256(payload, *args, **kwargs)

    monkeypatch.setattr(snapshot.json, "dumps", serialize)
    monkeypatch.setattr(snapshot.hashlib, "sha256", sha256)
    with pytest.raises(MemorySchemaError, match="request changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert observed == ["retarget"]


def test_unmodified_final_digest_remains_deterministic(tmp_path):
    store, request = _fixture(tmp_path)
    first = snapshot.review_coherent_snapshot(store, request)
    second = snapshot.review_coherent_snapshot(store, request)
    assert first == second
    assert len(first.provenance_sha256) == 64
