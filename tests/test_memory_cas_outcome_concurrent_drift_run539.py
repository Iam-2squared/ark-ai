"""Read-only CAS outcome review must reject writes between its two snapshots.

All side effects below are deliberately injected into an isolated SQLite fixture.
No automatic retry, external action, source identity or author attribution.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as review
from ark.memory import generation_fenced_cas as cas


@pytest.mark.parametrize("interleaving", ("identical_update", "divergent_update", "delete"))
def test_concurrent_writer_during_second_snapshot_denies_stale_report(
    tmp_path, monkeypatch, interleaving,
):
    path = tmp_path / "ambiguity.sqlite"
    scope = MemoryScope("run539", "private")
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    first = observer.put(
        MemoryWrite(scope, "fixture", "old", expires_at_ms=2000),
        expected_revision=0,
    )
    token = cas.observe_memory_generation_for_cas(observer, scope, "fixture")
    desired = MemoryWrite(scope, "fixture", "target", expires_at_ms=1900)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    triggered = []

    def interleave_once():
        if not triggered:
            triggered.append(interleaving)
            if interleaving == "delete":
                assert writer.delete(first.memory_id, scope, expected_revision=1)
            else:
                payload = "target" if interleaving == "identical_update" else "other"
                writer.put(
                    MemoryWrite(scope, "fixture", payload, expires_at_ms=1900),
                    expected_revision=1,
                )
        return False

    native_snapshot = review._snapshot
    observations = []

    def interleave_during_snapshot(*args):
        observed = native_snapshot(*args)
        observations.append(True)
        if len(observations) == 2:
            interleave_once()
        return observed

    monkeypatch.setattr(review, "_snapshot", interleave_during_snapshot)
    with pytest.raises(review.MemoryCASOutcomeRejected):
        review.review_memory_generation_cas_outcome(
            observer, desired, retained=token,
        )
    assert triggered == [interleaving]
    assert [e.operation for e in observer.events(scope)] == (
        ["create", "delete"] if interleaving == "delete" else ["create", "update"]
    )
    observed = writer.get(first.memory_id, scope, include_expired=True)
    if interleaving == "delete":
        assert observed is None
    else:
        assert observed is not None
        assert observed.revision == 2
        assert observed.content == (
            "target" if interleaving == "identical_update" else "other"
        )


@pytest.mark.parametrize("column,value", (
    ("operation", "delete"),
    ("revision", 3),
))
def test_event_history_tamper_during_second_snapshot_cannot_yield_outcome(
    tmp_path, monkeypatch, column, value,
):
    path = tmp_path / "events.sqlite"
    scope = MemoryScope("run539", "history")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    first = store.put(MemoryWrite(scope, "fixture", "old"), expected_revision=0)
    token = cas.observe_memory_generation_for_cas(store, scope, "fixture")
    desired = MemoryWrite(scope, "fixture", "new")
    triggered = []

    def tamper_once():
        if not triggered:
            triggered.append(column)
            with sqlite3.connect(path) as conn:
                conn.execute(
                    f"UPDATE memory_events SET {column}=? WHERE memory_id=?",
                    (value, first.memory_id),
                )
        return False

    native_snapshot = review._snapshot
    observations = []

    def tamper_during_snapshot(*args):
        observed = native_snapshot(*args)
        observations.append(True)
        if len(observations) == 2:
            tamper_once()
        return observed

    monkeypatch.setattr(review, "_snapshot", tamper_during_snapshot)
    with pytest.raises(review.MemoryCASOutcomeRejected):
        review.review_memory_generation_cas_outcome(
            store, desired, retained=token,
        )
    assert triggered == [column]
