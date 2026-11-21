"""Run949: a valid generation token cannot extend or revive expiring Memory.

These are local synthetic SQLite tests. A successful CAS is never consent,
trusted time, erasure proof, or authorization to dispatch an external tool.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(("proposed_expiry", "allowed"), (
    (None, False),
    (401, False),
    (400, True),
    (350, True),
))
def test_generation_retained_expiry_cannot_be_extended_or_cleared(
    tmp_path, proposed_expiry: int | None, allowed: bool,
) -> None:
    path = tmp_path / "bounded-lifetime.sqlite3"
    scope = MemoryScope("synthetic-owner", "private")
    original = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = original.put(
        MemoryWrite(scope, "private-source", "original", expires_at_ms=400),
    )
    token = observe_memory_generation_for_cas(original, scope, "private-source")
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    candidate = MemoryWrite(
        scope, "private-source", "updated", expires_at_ms=proposed_expiry,
    )

    if allowed:
        after = generation_fenced_memory_update(
            restarted, candidate, retained=token,
        )
        assert after.revision == 2
        assert after.expires_at_ms == proposed_expiry
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                restarted, candidate, retained=token,
            )
    else:
        with pytest.raises(MemoryGenerationCASRejected):
            generation_fenced_memory_update(
                restarted, candidate, retained=token,
            )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 250)
    record = cold.get(row.memory_id, scope)
    assert record is not None
    assert record.revision == (2 if allowed else 1)
    assert record.content == ("updated" if allowed else "original")
    assert record.expires_at_ms == (proposed_expiry if allowed else 400)
    with sqlite3.connect(path) as conn:
        sequence = conn.execute(
            "SELECT operation,revision FROM memory_events "
            "WHERE memory_id=? ORDER BY event_id", (row.memory_id,),
        ).fetchall()
    assert sequence == (
        [("create", 1), ("update", 2)]
        if allowed else [("create", 1)]
    )
    assert token.consent_authenticated is False
    assert token.external_action_authorized is False


@pytest.mark.parametrize(("writer_clock", "reason"), (
    (99, "regressed"),
    (400, "expired"),
    (401, "expired"),
))
def test_generation_cas_cannot_revive_expired_or_regressed_row(
    tmp_path, writer_clock: int, reason: str,
) -> None:
    path = tmp_path / "expiry-clock.sqlite3"
    scope = MemoryScope("synthetic-owner", "private")
    created = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = created.put(
        MemoryWrite(scope, "primary", "sealed", expires_at_ms=400),
    )
    observed = observe_memory_generation_for_cas(created, scope, "primary")
    with pytest.raises(MemoryConflictError, match=reason):
        generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: writer_clock),
            MemoryWrite(scope, "primary", "cannot-revive", expires_at_ms=400),
            retained=observed,
        )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    assert cold.get(row.memory_id, scope).content == "sealed"
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events",
        ).fetchone() == (1,)
