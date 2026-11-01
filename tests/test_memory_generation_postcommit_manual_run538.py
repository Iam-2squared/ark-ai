"""A generation CAS exception after SQLite COMMIT must not trigger automatic retry."""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome
from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemoryConflictError


@pytest.mark.parametrize("mutation", ("content", "metadata", "expiry"))
def test_post_commit_input_mutation_has_durable_row_and_manual_only_outcome(
    tmp_path, monkeypatch, mutation,
):
    path = tmp_path / "ambiguous.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("fixture", "manual")
    first = store.put(
        MemoryWrite(scope, "source", "first", expires_at_ms=3000),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(
        scope, "source", "second", {"origin": "fixture"}, expires_at_ms=2900,
    )
    original_closing = closing
    exits = []

    @contextmanager
    def after_commit_closing(conn):
        # The inner sqlite3.Connection context commits before this outer
        # closing context exits. This is a deterministic local fault fixture.
        with original_closing(conn) as handle:
            yield handle
            assert type(conn) is sqlite3.Connection
            exits.append("after-commit")
            if mutation == "content":
                object.__setattr__(proposed, "content", "retargeted")
            elif mutation == "metadata":
                object.__setattr__(proposed, "metadata", {"origin": "retargeted"})
            else:
                object.__setattr__(proposed, "expires_at_ms", 5000)

    monkeypatch.setattr(cas, "closing", after_commit_closing)
    with pytest.raises(cas.MemoryGenerationCASRejected, match="inputs changed"):
        cas.generation_fenced_memory_update(store, proposed, retained=retained)
    assert exits == ["after-commit"]

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    persisted = reopened.get(first.memory_id, scope, include_expired=True)
    assert persisted.revision == 2
    assert persisted.content == "second"
    assert dict(persisted.metadata) == {"origin": "fixture"}
    assert persisted.expires_at_ms == 2900
    assert [(e.operation, e.revision) for e in reopened.events(scope)] == [
        ("create", 1), ("update", 2),
    ]

    # Only read-only reconciliation is legal; never retry the old token.
    monkeypatch.setattr(cas, "closing", original_closing)
    observation = outcome.review_memory_generation_cas_outcome(
        reopened,
        MemoryWrite(scope, "source", "second", {"origin": "fixture"}, 2900),
        retained=retained,
    )
    assert observation.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    assert observation.commit_attributed_to_caller is False
    assert observation.automatic_retry_authorized is False
    assert observation.trusted_clock_verified is False
    with pytest.raises(MemoryConflictError, match="generation changed"):
        cas.generation_fenced_memory_update(
            reopened, MemoryWrite(scope, "source", "third", expires_at_ms=2800),
            retained=retained,
        )
    assert len(reopened.events(scope)) == 2
