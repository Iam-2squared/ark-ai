"""An already-created request must not invoke a replaced validator on review.

Local synthetic SQLite only; no external context source or action authority.
"""

import pytest

from ark.memory import coherent_snapshot_review as module
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "snapshot.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("synthetic-owner", "notes")
    saved = store.put(MemoryWrite(scope, "source", "local-only"))
    request = module.CoherentSnapshotRequest("synthetic-owner", ("notes",))
    return store, request, saved


@pytest.mark.parametrize("hook", ("__init__", "__post_init__"))
def test_forged_request_validator_cannot_execute(tmp_path, monkeypatch, hook):
    store, request, saved = _fixture(tmp_path)
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("forged request validator executed")

    monkeypatch.setattr(module.CoherentSnapshotRequest, hook, hostile)
    with pytest.raises(MemorySchemaError, match="request validator changed"):
        module.review_coherent_snapshot(store, request)
    assert executed == []
    assert store.get(saved.memory_id, saved.scope).content == "local-only"


def test_original_request_validation_preserves_coherent_read(tmp_path):
    store, request, saved = _fixture(tmp_path)
    result = module.review_coherent_snapshot(store, request)
    assert result.records[0][0].memory_id == saved.memory_id
    assert result.scopes == (saved.scope,)
    assert len(result.provenance_sha256) == 64
