"""Actual OS exit after Memory CAS commits: manual triage is not retry consent.

The caller retains its pre-write token independently of the worker. These
are disposable local SQLite fixtures, never proof of actor identity, external
effects, exact-once action, or authenticated consent.
"""

from __future__ import annotations

import os
from multiprocessing import get_context

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.postcommit_uncertainty_review import review_uncertain_memory_commit


def _commit_and_disappear(path, retained, mode):
    scope = MemoryScope("manual-triage-spawn", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 202)
    first = "unexpected-other-writer" if mode == "different" else "proposed"
    generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", first), retained=retained,
    )
    if mode == "twice":
        latest = observe_memory_generation_for_cas(store, scope, "source")
        generation_fenced_memory_update(
            store, MemoryWrite(scope, "source", "proposed"), retained=latest,
        )
    os._exit(0)  # No commit result reaches the waiting caller.


@pytest.mark.parametrize(
    ("mode", "disposition", "revision"),
    (
        ("matching", "ONE_MATCHING_UPDATE_VISIBLE", 2),
        ("different", "INDETERMINATE", 2),
        ("twice", "INDETERMINATE", 3),
    ),
)
def test_cold_manual_triage_after_lost_process_receipt(
    tmp_path, mode, disposition, revision,
):
    path = tmp_path / "memory-manual-triage-os-exit.sqlite3"
    scope = MemoryScope("manual-triage-spawn", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    original = first.put(MemoryWrite(scope, "source", "original"))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    proposed = MemoryWrite(scope, "source", "proposed")

    child = get_context("spawn").Process(
        target=_commit_and_disappear, args=(str(path), retained, mode),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0, "worker exited before expected COMMIT sequence"

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 210)
    before_events = tuple(cold.events(scope))
    before_row = cold.get(original.memory_id, scope)
    assert before_row is not None
    assert before_row.revision == revision
    assert len(before_events) == revision
    assert before_events[0].operation == "create"
    assert all(event.operation == "update" for event in before_events[1:])

    report = review_uncertain_memory_commit(
        cold, proposed, retained_before=retained,
    )
    assert report.disposition == disposition
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False
    assert tuple(cold.events(scope)) == before_events
    assert cold.get(original.memory_id, scope) == before_row

    # Even a visually matching post-COMMIT row cannot spend the old lifetime
    # token or justify repeating an ambiguous mutation.
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            cold, MemoryWrite(scope, "source", "never-auto-retry"),
            retained=retained,
        )
    assert tuple(cold.events(scope)) == before_events
