"""Run947: optional Memory generation-CAS refuses NUL identity separators.

Frozen v1 Memory contracts are untouched. Synthetic local CAS does not provide
writer authentication, consent, external effect or trusted-clock authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("field", ("owner_id", "namespace", "source_id"))
@pytest.mark.parametrize("fragment", ("\x00bad", "mid\x00dle", "bad\x00"))
def test_generation_cas_nul_identity_denied_without_persisted_change(
    tmp_path, field: str, fragment: str,
) -> None:
    path = tmp_path / "synthetic-generation-nul.sqlite3"
    scope = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "primary", "private-original"))
    token = observe_memory_generation_for_cas(store, scope, "primary")

    bad_scope = MemoryScope(
        fragment if field == "owner_id" else scope.owner_id,
        fragment if field == "namespace" else scope.namespace,
    )
    bad_source = fragment if field == "source_id" else "primary"
    candidate_scope = scope if field == "source_id" else bad_scope
    with pytest.raises(MemoryGenerationCASRejected):
        observe_memory_generation_for_cas(store, candidate_scope, bad_source)
    with pytest.raises(MemoryGenerationCASRejected):
        generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 200),
            MemoryWrite(candidate_scope, bad_source, "private-mutated"),
            retained=token,
        )

    assert store.get(original.memory_id, scope).content == "private-original"
    assert store.get(original.memory_id, scope).revision == 1
    with sqlite3.connect(path) as conn:
        events = conn.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall()
        assert events == [(1, "create", 1)]
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False


def test_valid_multibyte_generation_identity_still_can_advance_once(tmp_path) -> None:
    path = tmp_path / "synthetic-generation-unicode.sqlite3"
    scope = MemoryScope("所有者", "会話")
    original = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    first = original.put(MemoryWrite(scope, "資料", "初回"))
    token = observe_memory_generation_for_cas(original, scope, "資料")
    updated = generation_fenced_memory_update(
        SQLiteMemoryStore(path, clock_ms=lambda: 200),
        MemoryWrite(scope, "資料", "更新"),
        retained=token,
    )
    assert updated.memory_id == first.memory_id
    assert updated.revision == 2
    assert updated.content == "更新"
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
