"""Spawned-process SQLite generation-CAS and lost-response regression.

Synthetic, local Memory v1 only: winning a CAS does not authenticate an actor,
authorize a tool, or certify externally witnessed exactly-once execution.
The spawn context tests the same storage with independent Python interpreters
on Windows and Linux, not just separate threads in one interpreter.
"""

from __future__ import annotations

from multiprocessing import get_context
from queue import Empty

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _spawned_competing_writer(path, retained, value, release, messages):
    try:
        scope = MemoryScope("spawn-owner", "private")
        store = SQLiteMemoryStore(path, clock_ms=lambda: 300)
        messages.put((value, "ready", None))
        if not release.wait(30):
            raise RuntimeError("spawned CAS release timed out")
        try:
            written = generation_fenced_memory_update(
                store, MemoryWrite(scope, "source", value), retained=retained,
            )
        except MemoryConflictError:
            messages.put((value, "conflict", None))
        else:
            messages.put((value, "success", written.revision))
    except Exception as exc:
        messages.put((value, "error", repr(exc)))


def _spawned_commit_without_response(path, retained):
    # The process commits a local update and exits without handing the caller
    # any result object, modelling a lost response after COMMIT.
    scope = MemoryScope("spawn-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 301)
    generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "committed-without-receipt"),
        retained=retained,
    )


def _initial(tmp_path):
    path = tmp_path / "multiprocess-memory.sqlite3"
    scope = MemoryScope("spawn-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    row = store.put(MemoryWrite(scope, "source", "original"))
    token = observe_memory_generation_for_cas(store, scope, "source")
    return path, scope, row, token


@pytest.mark.parametrize("identical_content", [True, False])
def test_spawned_independent_writers_have_exactly_one_durable_cas_winner(
    tmp_path, identical_content,
):
    path, scope, original, token = _initial(tmp_path)
    context = get_context("spawn")
    release = context.Event()
    messages = context.Queue()
    labels = ("same", "same") if identical_content else ("first", "second")
    children = [
        context.Process(
            target=_spawned_competing_writer,
            args=(str(path), token, label, release, messages),
        )
        for label in labels
    ]
    try:
        # Initialize one independent SQLite handle at a time. Competing
        # first-open WAL sidecar cleanup is a distinct, fail-closed path
        # preflight and must not mask the actual CAS race under test.
        # The shared release event still starts BOTH CAS writes together.
        readiness = []
        for child in children:
            child.start()
            readiness.append(messages.get(timeout=35))
        assert sorted(item[1] for item in readiness) == ["ready", "ready"], readiness
        release.set()
        outcomes = [messages.get(timeout=35) for _ in children]
    except Empty as exc:
        pytest.fail(f"spawned writer did not report state: {exc}")
    finally:
        release.set()
        for child in children:
            child.join(timeout=20)
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
        messages.close()
        messages.join_thread()

    assert all(child.exitcode == 0 for child in children)
    assert sorted(item[1] for item in outcomes) == ["conflict", "success"], outcomes
    assert next(item[2] for item in outcomes if item[1] == "success") == 2
    fresh = SQLiteMemoryStore(path, clock_ms=lambda: 302)
    stored = fresh.get(original.memory_id, scope)
    assert stored is not None and stored.revision == 2
    assert stored.content == next(
        item[0] for item in outcomes if item[1] == "success"
    )
    assert len(fresh.events(scope)) == 2
    assert [event.operation for event in fresh.events(scope)] == ["create", "update"]
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            fresh, MemoryWrite(scope, "source", "replayed"), retained=token,
        )


def test_spawned_postcommit_lost_response_requires_manual_readback(tmp_path):
    path, scope, original, retained = _initial(tmp_path)
    context = get_context("spawn")
    child = context.Process(
        target=_spawned_commit_without_response, args=(str(path), retained),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    # No success receipt was delivered by the worker. Read durable state
    # instead of automatically replaying the ambiguous operation.
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 302)
    stored = cold.get(original.memory_id, scope)
    assert stored is not None
    assert stored.content == "committed-without-receipt"
    assert stored.revision == 2
    assert [event.operation for event in cold.events(scope)] == ["create", "update"]
    latest = observe_memory_generation_for_cas(cold, scope, "source")
    assert latest.create_event_id == retained.create_event_id
    assert latest.last_event_id > retained.last_event_id
    assert latest.revision == 2
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            cold, MemoryWrite(scope, "source", "duplicate"), retained=retained,
        )
