"""A detached Memory snapshot must not call a replaced result constructor.

No external context connector, action dispatch, or evidence authorization is used.
"""

import pytest

from ark.memory import coherent_snapshot_review as review
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "coherent.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("synthetic-owner", "private")
    saved = store.put(MemoryWrite(scope, "fixture", "content-free test"))
    request = review.CoherentSnapshotRequest("synthetic-owner", ("private",))
    return store, request, saved


@pytest.mark.parametrize("replacement", ("class", "constructor"))
def test_preinstalled_counterfeit_result_denied_without_execution(
    tmp_path, monkeypatch, replacement,
):
    store, request, saved = _case(tmp_path)
    executed = []

    def injected(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("counterfeit snapshot constructor executed")

    if replacement == "class":
        class CounterfeitResult:
            def __init__(self, *args, **kwargs):
                injected(*args, **kwargs)
        monkeypatch.setattr(review, "CoherentSnapshotReview", CounterfeitResult)
    else:
        monkeypatch.setattr(
            review.CoherentSnapshotReview, "__init__", injected,
        )

    with pytest.raises(MemorySchemaError, match="result constructor changed"):
        review.review_coherent_snapshot(store, request)
    assert executed == []
    assert store.get(saved.memory_id, saved.scope).content == "content-free test"


def test_reentrant_digest_callback_cannot_retarget_result_constructor(
    tmp_path, monkeypatch,
):
    store, request, saved = _case(tmp_path)
    executed = []
    triggered = []
    original_sha256 = review.hashlib.sha256

    def injected(*_args, **_kwargs):
        executed.append("executed")
        raise AssertionError("counterfeit snapshot constructor executed")

    def digest_with_mutation(payload=b""):
        if b'"witness_format_version":2' in payload:
            triggered.append("digest")
            monkeypatch.setattr(
                review.CoherentSnapshotReview, "__init__", injected,
            )
        return original_sha256(payload)

    monkeypatch.setattr(review.hashlib, "sha256", digest_with_mutation)
    with pytest.raises(MemorySchemaError, match="result constructor changed"):
        review.review_coherent_snapshot(store, request)
    assert triggered == ["digest"]
    assert executed == []
    assert store.get(saved.memory_id, saved.scope).content == "content-free test"


def test_original_snapshot_constructor_preserves_detached_read_only_result(tmp_path):
    store, request, saved = _case(tmp_path)
    actual = review.review_coherent_snapshot(store, request)
    assert type(actual) is review.CoherentSnapshotReview
    assert actual.scopes == (saved.scope,)
    assert actual.records[0][0].memory_id == saved.memory_id
    assert len(actual.provenance_sha256) == 64
