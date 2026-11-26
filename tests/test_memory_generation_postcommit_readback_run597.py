"""Post-COMMIT generation CAS readback must be locally coherent.

A failed post-commit check is UNKNOWN/manual review, NOT a rollback or
automatic retry. All test mutations use disposable SQLite files only.
"""

import hashlib
import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _setup(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "generation.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-owner", "private")
    record = store.put(MemoryWrite(scope, "fixture-source", "initial"))
    retained = cas.observe_memory_generation_for_cas(store, scope, "fixture-source")
    return store, scope, record, retained


def _update(store, scope, retained, content="updated post commit"):
    return cas.generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "fixture-source", content),
        retained=retained,
    )


def _persisted_state(store):
    with sqlite3.connect(store.path) as conn:
        revision = conn.execute("SELECT revision FROM memories").fetchone()[0]
        events = conn.execute("SELECT operation FROM memory_events ORDER BY event_id").fetchall()
    return revision, events


def test_normal_readback_preserves_atomic_update_and_never_replays(tmp_path):
    store, scope, _, token = _setup(tmp_path)
    result = _update(store, scope, token)
    assert result.revision == 2
    assert result.content == "updated post commit"
    assert _persisted_state(store) == (2, [("create",), ("update",)])


def test_readback_io_error_is_uncertain_not_a_retry_signal(tmp_path, monkeypatch):
    store, scope, _, token = _setup(tmp_path)

    def failed_readback():
        raise sqlite3.OperationalError("fixture failed post-COMMIT read")

    monkeypatch.setattr(store, "_connect_readonly", failed_readback)
    with pytest.raises(
        cas.MemoryGenerationCASRejected,
        match="post-COMMIT readback uncertain; manual review",
    ):
        _update(store, scope, token)
    # The original COMMIT happened. Do not allow clients to infer rollback.
    assert _persisted_state(store) == (2, [("create",), ("update",)])


@pytest.mark.parametrize("kind", ("content", "delete_event"))
def test_postcommit_sqlite_mutation_rejected_without_claiming_rollback(
    tmp_path, monkeypatch, kind,
):
    store, scope, _, token = _setup(tmp_path)
    real_read = store._connect_readonly

    def altered_read():
        with sqlite3.connect(store.path) as conn:
            if kind == "content":
                new_content = "tampered after commit"
                conn.execute(
                    "UPDATE memories SET content=?,content_sha256=?",
                    (new_content, hashlib.sha256(new_content.encode()).hexdigest()),
                )
            else:
                conn.execute("DELETE FROM memory_events WHERE operation='update'")
        return real_read()

    monkeypatch.setattr(store, "_connect_readonly", altered_read)
    with pytest.raises(cas.MemoryGenerationCASRejected, match="post-COMMIT"):
        _update(store, scope, token)
    assert _persisted_state(store)[0] == 2


def test_readback_callback_cannot_replace_committed_result_carrier(
    tmp_path, monkeypatch,
):
    store, scope, _, token = _setup(tmp_path)
    original = cas._snapshot
    calls = [0]
    committed = [None]

    def reflected_snapshot(conn, memory_id, scope, source_id):
        record, witness = original(conn, memory_id, scope, source_id)
        calls[0] += 1
        if calls[0] == 2:
            committed[0] = record
        elif calls[0] == 3:
            old = committed[0].content
            substitute = old.encode("utf-8").decode("utf-8")
            assert substitute == old and substitute is not old
            object.__setattr__(committed[0], "content", substitute)
        return record, witness

    monkeypatch.setattr(cas, "_snapshot", reflected_snapshot)
    with pytest.raises(
        cas.MemoryGenerationCASRejected,
        match="post-COMMIT readback result changed",
    ):
        _update(store, scope, token, content="long updated value with unique identity")
    assert calls[0] == 3
    assert _persisted_state(store) == (2, [("create",), ("update",)])
