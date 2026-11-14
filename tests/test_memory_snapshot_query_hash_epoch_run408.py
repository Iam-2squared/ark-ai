"""Snapshot query SHA-256 is an independent reentrancy boundary.

The digest is content-free continuity metadata, not consent, provenance or
permission for model/tool use. Tests use disposable offline SQLite only.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1100)
    scope = MemoryScope("owner-fixture", "private-fixture")
    store.put(MemoryWrite(scope, "source-fixture", "fixture text"))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), text="fixture",
    )
    return store, request


@pytest.mark.parametrize("target", ("request", "source", "record"))
def test_query_hash_mutation_is_rejected_before_later_json_can_restore(
    tmp_path, monkeypatch, target,
):
    store, request = _fixture(tmp_path)
    original_record = snapshot._record
    original_dumps = snapshot.json.dumps
    original_sha256 = snapshot.hashlib.sha256
    hydrated = []
    observed = []

    def hydrate(row):
        result = original_record(row)
        hydrated.append(result)
        return result

    def retarget():
        if target == "request":
            object.__setattr__(request, "text", "other-query")
        elif target == "source":
            store.path = Path(str(store.path))
        else:
            assert hydrated
            object.__setattr__(hydrated[0], "source_id", "other-source")
        observed.append("query-mutated")

    def hash_callback(payload=b"", *args, **kwargs):
        result = original_sha256(payload, *args, **kwargs)
        if payload == b"fixture":
            retarget()
        return result

    def restore_during_json(payload, **kwargs):
        if isinstance(payload, dict) and payload.get("witness_format_version") == 2:
            if target == "request":
                object.__setattr__(request, "text", "fixture")
            elif target == "source":
                store.path = Path(str(tmp_path / "memory.sqlite"))
            else:
                object.__setattr__(hydrated[0], "source_id", "source-fixture")
            observed.append("restored-by-json")
        return original_dumps(payload, **kwargs)

    monkeypatch.setattr(snapshot, "_record", hydrate)
    monkeypatch.setattr(snapshot.hashlib, "sha256", hash_callback)
    monkeypatch.setattr(snapshot.json, "dumps", restore_during_json)
    expected = {
        "request": "request changed",
        "source": "source path changed",
        "record": "record changed",
    }
    with pytest.raises(MemorySchemaError, match=expected[target]):
        snapshot.review_coherent_snapshot(store, request)
    assert observed == ["query-mutated"]
    assert len(hydrated) == 1


def test_unchanged_query_digest_remains_deterministic(tmp_path):
    store, request = _fixture(tmp_path)
    first = snapshot.review_coherent_snapshot(store, request)
    again = snapshot.review_coherent_snapshot(store, request)
    assert first == again
    assert len(first.provenance_sha256) == 64
