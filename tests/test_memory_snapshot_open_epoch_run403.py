"""Read-only Memory snapshot must retain its request at SQLite open boundaries.

Only disposable local SQLite fixtures are used. Nothing here accesses personal
data, performs a backend action, or modifies the frozen Memory v1 schema.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 500)
    scope = MemoryScope("offline-owner", "private")
    store.put(MemoryWrite(scope, "one", "fixture content"))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), per_namespace_limit=1,
    )
    return store, request


@pytest.mark.parametrize("mutation", ("owner", "namespaces", "path"))
def test_path_resolution_rejects_original_source_or_request_drift(
    tmp_path: Path, monkeypatch, mutation: str,
):
    store, request = _fixture(tmp_path)
    original_path = store.path
    original_resolve = Path.resolve
    observed = []

    def resolving(path, *args, **kwargs):
        resolved = original_resolve(path, *args, **kwargs)
        if path is original_path:
            observed.append("resolve")
            if mutation == "owner":
                object.__setattr__(request, "owner_id", "new-owner")
            elif mutation == "namespaces":
                object.__setattr__(
                    request, "namespaces", tuple(list(request.namespaces)),
                )
            else:
                store.path = Path(str(original_path))
        return resolved

    monkeypatch.setattr(Path, "resolve", resolving)
    with pytest.raises(MemorySchemaError, match="changed during review"):
        snapshot.review_coherent_snapshot(store, request)
    assert observed == ["resolve"]


def test_uri_construction_rechecks_request_before_open(tmp_path: Path, monkeypatch):
    store, request = _fixture(tmp_path)
    original_as_uri = Path.as_uri
    invoked = []

    def constructing_uri(path):
        uri = original_as_uri(path)
        invoked.append("uri")
        object.__setattr__(request, "text", "retargeted")
        return uri

    monkeypatch.setattr(Path, "as_uri", constructing_uri)
    with pytest.raises(MemorySchemaError, match="snapshot request changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert invoked == ["uri"]


@pytest.mark.parametrize("mutation", ("source", "query"))
def test_connection_open_rechecks_identity_before_first_select(
    tmp_path: Path, monkeypatch, mutation: str,
):
    store, request = _fixture(tmp_path)
    original_connect = sqlite3.connect
    opened = []

    def connecting(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(True)
        if mutation == "source":
            store.path = Path(str(store.path))
        else:
            object.__setattr__(request, "text", "substituted-query")
        return connection

    monkeypatch.setattr(snapshot.sqlite3, "connect", connecting)
    with pytest.raises(MemorySchemaError, match="changed during review"):
        snapshot.review_coherent_snapshot(store, request)
    assert opened == [True]

    with original_connect(tmp_path / "memory.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)


def test_unmodified_sqlite_open_keeps_content_minimized_snapshot(tmp_path: Path):
    store, request = _fixture(tmp_path)
    result = snapshot.review_coherent_snapshot(store, request)
    assert len(result.records) == 1
    assert len(result.records[0]) == 1
    assert len(result.provenance_sha256) == 64
