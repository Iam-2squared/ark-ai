"""Expiry filtering is an individual reentrant boundary in a Memory snapshot.

All cases are disconnected local SQLite fixtures. No personal data, deletion,
training or external ToolBackend is involved.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("offline-owner", "private")
    for index in range(3):
        store.put(MemoryWrite(
            scope, f"source-{index}", f"fixture content {index}",
        ))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), per_namespace_limit=3,
    )
    return store, request


@pytest.mark.parametrize(
    "mutation", ("record", "record_scope", "request_namespace", "store_path"),
)
def test_reflected_drift_during_second_expiry_is_rejected_before_third(
    tmp_path: Path, monkeypatch, mutation: str,
):
    store, request = _fixture(tmp_path)
    original_expired = snapshot._expired
    seen = []

    def expired(record, now):
        seen.append(record)
        if len(seen) == 2:
            first = seen[0]
            if mutation == "record":
                object.__setattr__(first, "content", "modified temporarily")
            elif mutation == "record_scope":
                object.__setattr__(first.scope, "namespace", "other")
            elif mutation == "request_namespace":
                object.__setattr__(request, "namespaces", ("other",))
            else:
                store.path = Path(str(store.path))
        elif len(seen) == 3:
            # On the vulnerable implementation this restored all changes
            # before ranking: an end-only check would incorrectly pass.
            first = seen[0]
            if mutation == "record":
                object.__setattr__(first, "content", "fixture content 0")
            elif mutation == "record_scope":
                object.__setattr__(first.scope, "namespace", "private")
            elif mutation == "request_namespace":
                object.__setattr__(request, "namespaces", ("private",))
            else:
                store.path = original_path
        return original_expired(record, now)

    original_path = store.path
    monkeypatch.setattr(snapshot, "_expired", expired)
    with pytest.raises(MemorySchemaError, match="changed during review"):
        snapshot.review_coherent_snapshot(store, request)
    assert len(seen) == 2


def test_unmodified_expiry_predicates_preserve_read_only_snapshot(tmp_path: Path):
    store, request = _fixture(tmp_path)
    result = snapshot.review_coherent_snapshot(store, request)
    assert len(result.records) == 1
    assert len(result.records[0]) == 3
    assert len(result.provenance_sha256) == 64


def test_include_expired_does_not_invoke_expiry_hook(tmp_path: Path, monkeypatch):
    store, request = _fixture(tmp_path)
    request = snapshot.CoherentSnapshotRequest(
        request.owner_id, request.namespaces,
        per_namespace_limit=3, include_expired=True,
    )

    def forbidden(*_args):
        raise AssertionError("expiry hook must be skipped")

    monkeypatch.setattr(snapshot, "_expired", forbidden)
    result = snapshot.review_coherent_snapshot(store, request)
    assert len(result.records[0]) == 3
