"""Two independent SQLite writers contend on generation-fenced Memory CAS.

Both subprocesses observe their retained generation before a common release
barrier. Same-row writers must serialize with one stale conflict; disjoint-row
writers can both commit. All state lives in disposable, synthetic SQLite files.
No external action, trusted clock or independent authorization is claimed.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

_CHILD = r"""
import pathlib
import sys
import time

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

path = pathlib.Path(sys.argv[1])
ready = pathlib.Path(sys.argv[2])
release = pathlib.Path(sys.argv[3])
source = sys.argv[4]
label = sys.argv[5]
scope = MemoryScope("synthetic-cas-race", "private")
store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
token = observe_memory_generation_for_cas(store, scope, source)
ready.touch()
deadline = time.monotonic() + 30
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit("release marker absent")
    time.sleep(0.02)
try:
    record = generation_fenced_memory_update(
        store, MemoryWrite(scope, source, label), retained=token,
    )
except MemoryConflictError:
    print("CONFLICT", flush=True)
else:
    assert record.revision == 2
    assert record.content == label
    print("COMMITTED", flush=True)
"""


def _barrier(paths, processes) -> None:
    deadline = time.monotonic() + 30
    while not all(path.exists() for path in paths):
        if any(proc.poll() is not None for proc in processes):
            raise AssertionError("Memory contender exited before common barrier")
        if time.monotonic() >= deadline:
            raise AssertionError("Memory contenders did not reach barrier")
        time.sleep(0.02)


@pytest.mark.parametrize("same_source", (True, False))
def test_cold_independent_writers_keep_row_event_cas_atomic(
    tmp_path, same_source: bool,
) -> None:
    path = tmp_path / "generation-writer-race.sqlite3"
    scope = MemoryScope("synthetic-cas-race", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    first = initial.put(MemoryWrite(scope, "source-a", "base-a"))
    if not same_source:
        initial.put(MemoryWrite(scope, "source-b", "base-b"))

    ready = [tmp_path / "a.ready", tmp_path / "b.ready"]
    release = tmp_path / "go"
    sources = ("source-a", "source-a" if same_source else "source-b")
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), str(ready[i]),
             str(release), source, f"updated-by-{i}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for i, source in enumerate(sources)
    ]
    outputs = []
    try:
        _barrier(ready, processes)
        release.touch()
        for proc in processes:
            stdout, stderr = proc.communicate(timeout=40)
            outputs.append((proc.returncode, stdout.strip(), stderr))
    finally:
        release.touch()
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    assert all(code == 0 and not stderr for code, _, stderr in outputs), outputs
    outcomes = sorted(message for _, message, _ in outputs)
    assert outcomes == (
        ["COMMITTED", "CONFLICT"] if same_source
        else ["COMMITTED", "COMMITTED"]
    )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    events = cold.events(scope)
    if same_source:
        assert [(e.event_id, e.operation, e.revision) for e in events] == [
            (1, "create", 1), (2, "update", 2),
        ]
        result = cold.get(first.memory_id, scope)
        assert result is not None and result.revision == 2
        assert result.content in ("updated-by-0", "updated-by-1")
    else:
        assert [e.operation for e in events] == [
            "create", "create", "update", "update",
        ]
        assert sorted(e.revision for e in events if e.operation == "update") == [2, 2]
