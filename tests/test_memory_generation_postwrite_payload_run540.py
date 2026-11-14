"""Opt-in Memory generation CAS verifies the exact final row inside its write.

A reflected event hook may rewrite metadata or retention before COMMIT. Such
reentrant edits must roll back both the local row and event in the same
SQLite transaction; this test never grants live action or retry authority.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "generation.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("run540", "retained")
    first = store.put(
        MemoryWrite(
            scope, "source", "before",
            {"origin": "prior"}, expires_at_ms=4000,
        ), expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(
        scope, "source", "after",
        {"origin": "proposed"}, expires_at_ms=3900,
    )
    return store, scope, first, retained, proposed


def test_exact_postwrite_metadata_and_expiry_survive_normal_commit(tmp_path):
    store, scope, _, retained, proposed = _case(tmp_path)
    result = cas.generation_fenced_memory_update(
        store, proposed, retained=retained,
    )
    assert result.revision == 2
    assert result.content == "after"
    assert dict(result.metadata) == {"origin": "proposed"}
    assert result.expires_at_ms == 3900
    assert result.updated_at_ms == 1000
    assert [event.operation for event in store.events(scope)] == [
        "create", "update",
    ]


@pytest.mark.parametrize("field", ("metadata", "expiry"))
def test_reentrant_event_hook_cannot_change_committed_payload_or_retention(
    tmp_path, monkeypatch, field,
):
    store, scope, first, retained, proposed = _case(tmp_path)
    baseline = store.get(first.memory_id, scope, include_expired=True)
    history = store.events(scope)
    original = SQLiteMemoryStore._event
    seen = []

    def tamper(conn, memory_id, event_scope, operation, revision, occurred_at_ms):
        original(
            conn, memory_id, event_scope, operation, revision, occurred_at_ms,
        )
        if operation == "update":
            seen.append(field)
            if field == "metadata":
                conn.execute(
                    "UPDATE memories SET metadata_json=? WHERE memory_id=?",
                    ('{"origin":"forged"}', memory_id),
                )
            else:
                conn.execute(
                    "UPDATE memories SET expires_at_ms=? WHERE memory_id=?",
                    (5000, memory_id),
                )

    monkeypatch.setattr(SQLiteMemoryStore, "_event", staticmethod(tamper))
    with pytest.raises(cas.MemoryGenerationCASRejected, match="postwrite"):
        cas.generation_fenced_memory_update(
            store, proposed, retained=retained,
        )
    assert seen == [field]
    # Atomic rejection: the entire original write transaction is rolled back,
    # rather than preserving a row with an unrelated event or a forged expiry.
    assert store.get(first.memory_id, scope, include_expired=True) == baseline
    assert store.events(scope) == history
    observed = cas.observe_memory_generation_for_cas(store, scope, "source")
    assert observed == retained
