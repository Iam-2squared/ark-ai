"""Opt-in generation CAS identities have a strict UTF-8 *byte* budget.

The frozen Memory v1 character-count contract is not rewritten here. The
additional optional CAS rule rejects ambiguous over-budget source identities
before SQLite access; local clocks are synthetic and grant no authority.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("source", ("a" * 512, "é" * 256))
def test_exact_512_utf8_bytes_support_generation_fenced_update(tmp_path, source):
    clock = [1000]
    store = SQLiteMemoryStore(
        tmp_path / "boundary.sqlite", clock_ms=lambda: clock[0],
    )
    scope = MemoryScope("local-owner", "fixtures")
    first = store.put(MemoryWrite(scope, source, "before"))
    token = observe_memory_generation_for_cas(store, scope, source)
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False

    clock[0] = 1001
    after = generation_fenced_memory_update(
        store, MemoryWrite(scope, source, "after"), retained=token,
    )
    assert after.memory_id == first.memory_id
    assert after.revision == 2
    assert after.content == "after"
    assert tuple(event.operation for event in store.events(scope)) == (
        "create", "update",
    )


@pytest.mark.parametrize("source", ("é" * 257, "あ" * 171))
def test_multibyte_over_budget_identity_is_rejected_before_cas(tmp_path, source):
    store = SQLiteMemoryStore(tmp_path / "over-budget.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("local-owner", "fixtures")
    # This is a valid legacy Memory v1 *character-count* identifier.
    original = store.put(MemoryWrite(scope, source, "legacy"))
    events = store.events(scope)

    with pytest.raises(MemoryGenerationCASRejected, match="512 UTF-8 bytes"):
        observe_memory_generation_for_cas(store, scope, source)

    assert store.events(scope) == events
    assert store.get(original.memory_id, scope) == original


def test_surrogate_source_is_rejected_without_unhandled_encoding_error(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "invalid-utf8.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("local-owner", "fixtures")
    with pytest.raises(MemoryGenerationCASRejected, match="valid UTF-8"):
        observe_memory_generation_for_cas(store, scope, "bad\ud800identity")
    assert store.events(scope) == []


def test_reflected_invalid_write_source_cannot_reuse_old_token(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "changed-utf8.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("local-owner", "fixtures")
    store.put(MemoryWrite(scope, "valid", "first"))
    token = observe_memory_generation_for_cas(store, scope, "valid")
    write = MemoryWrite(scope, "valid", "second")
    object.__setattr__(write, "source_id", "bad\ud800identity")
    events = store.events(scope)

    with pytest.raises(MemoryGenerationCASRejected, match="valid UTF-8"):
        generation_fenced_memory_update(store, write, retained=token)
    assert store.events(scope) == events


def test_unbounded_direct_observation_is_rejected_before_sqlite(monkeypatch, tmp_path):
    store = SQLiteMemoryStore(tmp_path / "direct-oversize.sqlite")
    scope = MemoryScope("local-owner", "fixtures")

    def forbidden():
        pytest.fail("unbounded source must be rejected before SQLite read")

    monkeypatch.setattr(store, "_connect_readonly", forbidden)
    with pytest.raises(MemoryGenerationCASRejected, match="512 UTF-8 bytes"):
        observe_memory_generation_for_cas(store, scope, "a" * 100_000)
