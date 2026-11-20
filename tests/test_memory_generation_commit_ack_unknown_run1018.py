"""Run1018: a lost native COMMIT acknowledgement is Memory UNKNOWN, not retry."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.postcommit_uncertainty_review import review_uncertain_memory_commit


def test_native_commit_acknowledgement_loss_keeps_row_event_pair_and_denies_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "generation-commit-unknown.sqlite3"
    scope = MemoryScope("run1018-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    created = store.put(
        MemoryWrite(scope, "stable", "before"),
        expected_revision=0,
    )
    retained = observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(
        scope,
        "stable",
        "after",
        metadata={"origin": "synthetic"},
    )

    native_connect = store._connect
    native_commits: list[bool] = []

    class CommitAcknowledgementLost:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def __enter__(self):
            # Match sqlite3.Connection's context-manager return contract.
            return self

        def __exit__(self, exc_type, exc, traceback):
            result = self.connection.__exit__(exc_type, exc, traceback)
            if exc_type is None:
                # The native context has committed successfully. Only the
                # acknowledgement to generation_fenced_memory_update is lost.
                native_commits.append(True)
                raise sqlite3.OperationalError(
                    "synthetic COMMIT acknowledgement lost",
                )
            return result

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect_with_lost_acknowledgement():
        return CommitAcknowledgementLost(native_connect())

    monkeypatch.setattr(store, "_connect", connect_with_lost_acknowledgement)
    with pytest.raises(
        MemoryGenerationCASRejected,
        match="generation CAS SQLite outcome uncertain",
    ):
        generation_fenced_memory_update(
            store,
            proposed,
            retained=retained,
        )

    assert native_commits == [True]

    # A new process/handle can see the durable row/event pair, but cannot
    # attribute the native COMMIT to the caller that lost its acknowledgement.
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1001)
    persisted = reopened.get(created.memory_id, scope, include_expired=True)
    assert persisted is not None
    assert (
        persisted.content,
        dict(persisted.metadata),
        persisted.revision,
    ) == ("after", {"origin": "synthetic"}, 2)
    assert [
        (event.event_id, event.operation, event.revision)
        for event in reopened.events(scope)
    ] == [(1, "create", 1), (2, "update", 2)]

    report = review_uncertain_memory_commit(
        reopened,
        proposed,
        retained_before=retained,
    )
    assert report.disposition == "ONE_MATCHING_UPDATE_VISIBLE"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False

    # The original lifetime token cannot be replayed after the unknown commit.
    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            reopened,
            proposed,
            retained=retained,
        )
    assert reopened.get(created.memory_id, scope, include_expired=True) == persisted
    assert [
        (event.event_id, event.operation, event.revision)
        for event in reopened.events(scope)
    ] == [(1, "create", 1), (2, "update", 2)]
