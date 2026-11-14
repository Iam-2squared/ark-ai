"""Deterministic multi-scope Memory CAS state machine across two SQLite handles.

All records and deletes belong to disposable tmp_path fixtures. This tests local
CAS/event invariants only, not trusted identity, secure erasure or authorization.
"""

from __future__ import annotations

import random

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
    deterministic_memory_id,
)
from ark.memory import generation_fenced_cas as cas
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize("seed", [11, 43, 97])
def test_multiscope_restart_cas_lifecycle_matches_event_model(tmp_path, seed):
    rng = random.Random(seed)
    now = {"ms": 10_000}

    def clock():
        return now["ms"]

    path = tmp_path / "generation-model.db"
    writers = (
        SQLiteMemoryStore(path, clock_ms=clock),
        SQLiteMemoryStore(path, clock_ms=clock),
    )
    keys = tuple(
        (MemoryScope("synthetic-owner-" + str(i), "notes"), "note-" + str(j))
        for i in range(2) for j in range(3)
    )
    active = {}
    mutations = 0
    denied = 0

    for step in range(48):
        scope, source = rng.choice(keys)
        writer = writers[step % 2]
        key = (scope, source)
        current = active.get(key)
        now["ms"] += 1

        if current is None:
            record = writer.put(
                MemoryWrite(scope, source, f"fresh {seed}:{step}"),
                expected_revision=0,
            )
            assert record.revision == 1
            active[key] = record
            mutations += 1
        elif rng.randrange(4) != 0:
            retained = cas.observe_memory_generation_for_cas(writer, scope, source)
            assert retained.revision == current.revision
            assert retained.memory_id == current.memory_id
            assert retained.external_action_authorized is False
            record = cas.generation_fenced_memory_update(
                writer,
                MemoryWrite(scope, source, f"update {seed}:{step}"),
                retained=retained,
            )
            assert record.revision == current.revision + 1
            active[key] = record
            mutations += 1
            # Previously observed generations are one-shot, including when
            # a competing handle has already observed the new revision.
            with pytest.raises(MemoryConflictError, match="generation changed"):
                cas.generation_fenced_memory_update(
                    writers[(step + 1) % 2],
                    MemoryWrite(scope, source, "invalid stale update"),
                    retained=retained,
                )
            denied += 1
        else:
            assert writer.delete(
                current.memory_id, scope, expected_revision=current.revision,
            ) is True
            assert writer.delete(
                current.memory_id, scope, expected_revision=current.revision,
            ) is False
            del active[key]
            mutations += 1

        # Every denied replay must leave the global append count unchanged.
        audit = review_memory_event_alignment(writers[(step + 1) % 2])
        assert audit.row_count == len(active)
        assert audit.event_count == mutations
        assert audit.last_event_id == mutations
        assert audit.independently_authenticated is False
        assert audit.action_authorized is False
        for known_scope, known_source in keys:
            identity = deterministic_memory_id(known_scope, known_source)
            observed = writers[step % 2].get(
                identity, known_scope, include_expired=True,
            )
            expected = active.get((known_scope, known_source))
            assert observed == expected

    assert mutations == 48
    assert denied > 0
    # Closed lifetimes may be reopened under the same deterministic memory ID.
    # A live row is always justified by a create event in its latest lifetime.
    assert review_memory_event_alignment(writers[0]).row_count == len(active)
