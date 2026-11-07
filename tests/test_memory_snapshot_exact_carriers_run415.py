"""Memory snapshot cannot silently accept equal-value source identity swaps.

The immutable review is disconnected, content-minimized evidence; it neither
exports private memory nor authenticates user consent or backend actions.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(
        MemoryScope("fixture-owner", "private"), "source", "PRIVATE-CONTENT",
    ))
    request = snapshot.CoherentSnapshotRequest(
        "fixture-owner", ("private",), text="PRIVATE",
    )
    return store, request


def _clone(value: str) -> str:
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


@pytest.mark.parametrize("field", ("owner_id", "text"))
def test_query_tokenization_cannot_rebind_original_request_carrier(
    tmp_path: Path, monkeypatch, field: str,
):
    store, request = _fixture(tmp_path)
    original = snapshot._tokens
    called = []

    def changed(text):
        result = original(text)
        if not called:
            called.append(True)
            object.__setattr__(request, field, _clone(getattr(request, field)))
        return result

    monkeypatch.setattr(snapshot, "_tokens", changed)
    with pytest.raises(snapshot.MemorySchemaError, match="snapshot request changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert called == [True]


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_query_tokenization_cannot_rebind_new_snapshot_scope(
    tmp_path: Path, monkeypatch, field: str,
):
    store, request = _fixture(tmp_path)
    existing_post_init = MemoryScope.__post_init__
    existing_tokens = snapshot._tokens
    created = []
    called = []

    def observe(self):
        existing_post_init(self)
        created.append(self)

    def changed(text):
        result = existing_tokens(text)
        if not called:
            assert created
            called.append(True)
            target = created[-1]
            object.__setattr__(target, field, _clone(getattr(target, field)))
        return result

    monkeypatch.setattr(MemoryScope, "__post_init__", observe)
    monkeypatch.setattr(snapshot, "_tokens", changed)
    with pytest.raises(snapshot.MemorySchemaError, match="snapshot scope changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert called == [True]


def test_unchanged_private_snapshot_keeps_content_out_of_digest(tmp_path: Path):
    store, request = _fixture(tmp_path)
    result = snapshot.review_coherent_snapshot(store, request)
    assert result.scopes[0].owner_id == "fixture-owner"
    assert result.records[0][0].content == "PRIVATE-CONTENT"
    assert len(result.provenance_sha256) == 64
    assert "PRIVATE-CONTENT" not in result.provenance_sha256
