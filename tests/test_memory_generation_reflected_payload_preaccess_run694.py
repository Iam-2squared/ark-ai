"""Opt-in CAS rejects malformed reflected writes before private SQLite.

MemoryWrite is frozen but its fields can be changed via object.__setattr__.
Only the opt-in lifetime CAS is hardened; frozen v1 semantics are untouched.
A definitive pre-transaction rejection does not attribute COMMIT-UNKNOWN,
grant permission or authorize replay of a potentially committed update.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("content", "", "content"),
        ("content", "  ", "content"),
        ("content", 23, "content"),
        ("content", "x" * 1_000_001, "content"),
        ("expires_at_ms", True, "expiry"),
        ("expires_at_ms", -1, "expiry"),
        ("expires_at_ms", 2**63, "expiry"),
        ("expires_at_ms", "unbounded", "expiry"),
        ("metadata", {"": "value"}, "metadata"),
        ("metadata", {"label": 2}, "metadata"),
        ("metadata", {"label": "a" * 4097}, "metadata"),
        ("metadata", {"a" * 4097: "value"}, "metadata"),
        ("metadata", {str(i): "value" for i in range(65)}, "metadata"),
        ("metadata", ["not", "a", "mapping"], "metadata"),
        ("metadata", {"\ud800": "value"}, "UTF-8"),
        ("metadata", {"label": "\udfff"}, "UTF-8"),
    ),
)
def test_reflected_invalid_cas_write_never_opens_private_transaction(
    tmp_path, monkeypatch, field, value, reason,
):
    path = tmp_path / "source.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    old = store.put(MemoryWrite(scope, "source", "before", expires_at_ms=500))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(scope, "source", "after", expires_at_ms=500)
    object.__setattr__(proposed, field, value)
    opened = []

    def forbidden_write_connection():
        opened.append("write")
        pytest.fail("invalid CAS payload reached private SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", forbidden_write_connection)
        with pytest.raises(MemoryGenerationCASRejected, match=reason):
            generation_fenced_memory_update(store, proposed, retained=retained)
    assert opened == []
    fresh = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert fresh.get(old.memory_id, scope).content == "before"
    assert fresh.get(old.memory_id, scope).revision == 1
    assert len(fresh.events(scope)) == 1
    assert observe_memory_generation_for_cas(fresh, scope, "source") == retained
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    # The rejected, pre-transaction proposal consumed no local CAS token.
    # This is NOT a permission to retry an ambiguous post-COMMIT write.
    valid = generation_fenced_memory_update(
        fresh,
        MemoryWrite(scope, "source", "accepted", expires_at_ms=500),
        retained=retained,
    )
    assert valid.revision == 2
    assert len(fresh.events(scope)) == 2


@pytest.mark.parametrize(
    "metadata",
    (
        {"label": "x" * 4096},
        {f"key-{i}": "value" for i in range(64)},
        {"場所": "山", "kind": "🧪"},
    ),
)
def test_maximum_valid_metadata_remains_local_and_cas_updatable(
    tmp_path, metadata,
):
    path = tmp_path / "valid.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "source", "before", expires_at_ms=500))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    updated = generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "source", "after", metadata, expires_at_ms=500),
        retained=retained,
    )
    assert updated.memory_id == original.memory_id
    assert updated.revision == 2
    assert dict(updated.metadata) == metadata
    assert updated.content == "after"
    assert len(store.events(scope)) == 2
    assert observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 100), scope, "source",
    ).last_event_id > retained.last_event_id
