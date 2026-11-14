"""Coherent Memory snapshots reject equal-value hydrated carrier substitutions.

All rows live in disposable local SQLite. Returned digests are content-minimized
diagnostics, not identity, consent, or permission to disclose personal data.
"""

from types import MappingProxyType

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1100)
    scope = MemoryScope("fixture-owner", "private")
    for index in range(2):
        store.put(MemoryWrite(
            scope, f"source-{index}", f"needle-content-{index}",
            {"origin": f"fixture-{index}"}, expires_at_ms=5000,
        ))
    request = snapshot.CoherentSnapshotRequest(
        scope.owner_id, (scope.namespace,), text="needle",
    )
    return store, request


def _new_string(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize("mutation", (
    "scope", "metadata", "memory_id", "source_id", "content",
    "content_sha256", "owner", "namespace", "created_at_ms",
    "updated_at_ms", "expires_at_ms",
))
def test_hydrated_record_cannot_be_retargeted_to_equal_carrier(
    tmp_path, monkeypatch, mutation,
):
    store, request = _fixture(tmp_path)
    observed = []
    original_hydrate = snapshot._record
    original_tokens = snapshot._tokens
    changed = []

    def hydrate(row):
        item = original_hydrate(row)
        observed.append(item)
        return item

    def tokens(text):
        result = original_tokens(text)
        if observed and not changed:
            changed.append(True)
            item = observed[0]
            if mutation == "scope":
                object.__setattr__(
                    item, "scope",
                    MemoryScope(item.scope.owner_id, item.scope.namespace),
                )
            elif mutation == "metadata":
                object.__setattr__(
                    item, "metadata", MappingProxyType(dict(item.metadata)),
                )
            elif mutation in {"owner", "namespace"}:
                field = "owner_id" if mutation == "owner" else "namespace"
                object.__setattr__(
                    item.scope, field, _new_string(getattr(item.scope, field)),
                )
            elif mutation in {"created_at_ms", "updated_at_ms", "expires_at_ms"}:
                value = getattr(item, mutation)
                replacement = int(str(value))
                assert replacement == value and replacement is not value
                object.__setattr__(item, mutation, replacement)
            else:
                object.__setattr__(
                    item, mutation, _new_string(getattr(item, mutation)),
                )
        return result

    monkeypatch.setattr(snapshot, "_record", hydrate)
    monkeypatch.setattr(snapshot, "_tokens", tokens)
    with pytest.raises(MemorySchemaError, match="memory snapshot record changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert changed == [True]


def test_unchanged_two_record_snapshot_is_content_minimized(tmp_path):
    store, request = _fixture(tmp_path)
    result = snapshot.review_coherent_snapshot(store, request)
    assert len(result.records[0]) == 2
    assert result == snapshot.review_coherent_snapshot(store, request)
    assert len(result.provenance_sha256) == 64
    assert "needle-content" not in result.provenance_sha256
