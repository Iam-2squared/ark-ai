"""A post-COMMIT readback error is UNKNOWN, never a replay invitation.

Disposable SQLite with deterministic local time. No external tool actions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import (
    MemoryConflictError,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("failure", ("sqlite", "schema"))
def test_postcommit_readback_failure_preserves_durable_write_and_stale_cas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(
        tmp_path / "generation.sqlite", clock_ms=lambda: 100,
    )
    initial = store.put(MemoryWrite(scope, "one-source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "one-source")
    proposal = MemoryWrite(scope, "one-source", "committed-but-unknown")

    def fail_readback():
        if failure == "sqlite":
            raise sqlite3.OperationalError("synthetic readback outage")
        raise MemorySchemaError("synthetic readback validation outage")

    # The mutation takes place on the original writer connection. Only its
    # *postcommit* readback fails. A caller cannot infer rollback from error.
    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", fail_readback)
        with pytest.raises(
            MemoryGenerationCASRejected, match="post-COMMIT readback",
        ):
            generation_fenced_memory_update(
                store, proposal, retained=retained,
            )

    persisted = store.get(initial.memory_id, scope)
    assert persisted is not None
    assert persisted.content == "committed-but-unknown"
    assert persisted.revision == 2
    assert [
        (event.operation, event.revision) for event in store.events(scope)
    ] == [("create", 1), ("update", 2)]

    # This is not a retryable error: the original lifetime token is stale.
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            store, proposal, retained=retained,
        )
    after = store.get(initial.memory_id, scope)
    assert after == persisted
    assert len(store.events(scope)) == 2
