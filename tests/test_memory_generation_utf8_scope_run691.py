"""Opt-in generation identity scopes are strict UTF-8 byte-bounded inputs.

The frozen Memory v1 scope contract remains character-bounded. These local
fixtures only exercise generation-CAS and manual outcome review; no identity,
consent, external action or automatic retry is established.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("owner", "namespace", "message"),
    (
        ("bad\ud800", "fixtures", "valid UTF-8"),
        ("owner", "bad\udfff", "valid UTF-8"),
        ("é" * 129, "fixtures", "256 UTF-8 bytes"),
        ("owner", "あ" * 86, "256 UTF-8 bytes"),
    ),
)
def test_invalid_legacy_scope_is_denied_before_generation_sqlite_read(
    tmp_path, monkeypatch, owner, namespace, message,
):
    scope = MemoryScope(owner, namespace)
    store = SQLiteMemoryStore(tmp_path / "scope.sqlite", clock_ms=lambda: 100)

    def forbidden():
        pytest.fail("malformed generation scope must be denied before SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden)
    with pytest.raises(MemoryGenerationCASRejected, match=message):
        observe_memory_generation_for_cas(store, scope, "fixture")


@pytest.mark.parametrize(
    "invalid_scope",
    (
        MemoryScope("bad\ud800", "private"),
        MemoryScope("owner", "bad\udfff"),
        MemoryScope("é" * 129, "private"),
        MemoryScope("owner", "あ" * 86),
    ),
)
def test_mutated_write_scope_is_rejected_without_consuming_valid_cas(
    tmp_path, invalid_scope,
):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "fixture", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "fixture")
    forged = MemoryWrite(scope, "fixture", "after")
    object.__setattr__(forged, "scope", invalid_scope)
    with pytest.raises(MemoryGenerationCASRejected):
        generation_fenced_memory_update(store, forged, retained=retained)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert cold.get(original.memory_id, scope).content == "before"
    assert len(cold.events(scope)) == 1
    assert observe_memory_generation_for_cas(cold, scope, "fixture") == retained


def test_outcome_review_rejects_invalid_scope_before_private_sqlite(
    tmp_path, monkeypatch,
):
    path = tmp_path / "private.sqlite"
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "fixture", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "fixture")
    proposed = MemoryWrite(scope, "fixture", "after")
    object.__setattr__(
        proposed, "scope", MemoryScope("owner", "bad\ud800"),
    )

    def forbidden():
        pytest.fail("manual outcome review must not read malformed scope")

    monkeypatch.setattr(store, "_connect_readonly", forbidden)
    with pytest.raises(MemoryCASOutcomeRejected, match="valid UTF-8 scope"):
        review_memory_generation_cas_outcome(store, proposed, retained=retained)


def test_maximum_valid_multibyte_scope_can_update_without_authority(tmp_path):
    scope = MemoryScope("é" * 128, "あ" * 85)
    path = tmp_path / "bounded.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    initial = store.put(MemoryWrite(scope, "fixture", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "fixture")
    assert retained.external_action_authorized is False
    result = generation_fenced_memory_update(
        store, MemoryWrite(scope, "fixture", "after"), retained=retained,
    )
    assert result.memory_id == initial.memory_id
    assert result.revision == 2
    assert SQLiteMemoryStore(
        path, clock_ms=lambda: 100,
    ).get(initial.memory_id, scope).content == "after"
    assert len(store.events(scope)) == 2
