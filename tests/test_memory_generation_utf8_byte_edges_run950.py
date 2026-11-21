"""Run950: optional generation CAS uses exact UTF-8 byte budgets.

Synthetic local Memory rows only; these witnesses do not grant consent,
trusted time, backend execution or independent writer authentication.
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


@pytest.mark.parametrize(("field", "four_byte_chars", "accepted"), (
    ("owner_id", 64, True),
    ("owner_id", 65, False),
    ("namespace", 64, True),
    ("namespace", 65, False),
    ("source_id", 128, True),
    ("source_id", 129, False),
))
def test_generation_identity_admits_only_bounded_encoded_bytes(
    tmp_path, field: str, four_byte_chars: int, accepted: bool,
) -> None:
    path = tmp_path / "synthetic-utf8-generation.sqlite3"
    base = MemoryScope("synthetic-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(base, "primary", "private-baseline"))
    baseline = observe_memory_generation_for_cas(store, base, "primary")

    identifier = "🪐" * four_byte_chars
    target = MemoryScope(
        identifier if field == "owner_id" else base.owner_id,
        identifier if field == "namespace" else base.namespace,
    )
    scope = base if field == "source_id" else target
    source = identifier if field == "source_id" else "primary"
    proposal = MemoryWrite(scope, source, "synthetic-updated")

    if accepted:
        record = store.put(MemoryWrite(scope, source, "synthetic-original"))
        token = observe_memory_generation_for_cas(store, scope, source)
        updated = generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 200),
            proposal, retained=token,
        )
        assert updated.memory_id == record.memory_id
        assert updated.revision == 2
        assert updated.content == "synthetic-updated"
        assert token.consent_authenticated is False
        assert token.external_action_authorized is False
    else:
        # Legacy Memory v1 accepts character-bounded Unicode. Only the
        # opt-in CAS entrypoint applies this stricter byte-level guard.
        with pytest.raises(MemoryGenerationCASRejected):
            observe_memory_generation_for_cas(store, scope, source)
        with pytest.raises(MemoryGenerationCASRejected):
            generation_fenced_memory_update(
                SQLiteMemoryStore(path, clock_ms=lambda: 200),
                proposal, retained=baseline,
            )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    assert cold.get(original.memory_id, base).content == "private-baseline"
    with sqlite3.connect(path) as conn:
        events = conn.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id"
        ).fetchall()
    assert [event_id for event_id, _ in events] == list(
        range(1, len(events) + 1)
    )
    assert len(events) == (3 if accepted else 1)
    assert baseline.consent_authenticated is False
    assert baseline.external_action_authorized is False
