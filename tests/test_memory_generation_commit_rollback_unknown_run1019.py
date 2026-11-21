"""Run1019: a pre-native-COMMIT failure leaves Memory CAS unchanged."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.postcommit_uncertainty_review import review_uncertain_memory_commit


def test_precommit_failure_rolls_back_memory_row_and_event_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "generation-precommit-rollback.sqlite3"
    scope = MemoryScope("run1019-owner", "private")
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
    commit_attempts: list[bool] = []
    native_commits: list[bool] = []
    rollbacks: list[bool] = []

    class CommitFailsBeforeNative:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            if exc_type is None:
                # The failure occurs at the COMMIT boundary; native COMMIT is
                # deliberately not invoked. Model the rollback outcome.
                commit_attempts.append(True)
                self.connection.rollback()
                rollbacks.append(True)
                raise sqlite3.OperationalError(
                    "synthetic Memory COMMIT failure before native commit",
                )
            return self.connection.__exit__(exc_type, exc, traceback)

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect_with_precommit_failure():
        return CommitFailsBeforeNative(native_connect())

    monkeypatch.setattr(store, "_connect", connect_with_precommit_failure)
    with pytest.raises(
        MemoryGenerationCASRejected,
        match="generation CAS SQLite outcome uncertain",
    ):
        generation_fenced_memory_update(
            store,
            proposed,
            retained=retained,
        )

    assert commit_attempts == [True]
    assert native_commits == []
    assert rollbacks == [True]

    # Cold readback distinguishes this synthetic rollback outcome from PR #67's
    # committed-but-unacknowledged row/event pair. It grants no retry authority.
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1001)
    persisted = reopened.get(created.memory_id, scope, include_expired=True)
    assert persisted is not None
    assert (
        persisted.content,
        dict(persisted.metadata),
        persisted.revision,
    ) == ("before", {}, 1)
    assert [
        (event.event_id, event.operation, event.revision)
        for event in reopened.events(scope)
    ] == [(1, "create", 1)]

    report = review_uncertain_memory_commit(
        reopened,
        proposed,
        retained_before=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False

    assert reopened.get(created.memory_id, scope, include_expired=True) == persisted
    assert [
        (event.event_id, event.operation, event.revision)
        for event in reopened.events(scope)
    ] == [(1, "create", 1)]
