"""Independent SQLite Memory creation races validate revision-zero CAS.

Only disposable local databases and mock owners/sources are used. These tests
exercise durable Memory events, not consent, external action, or notification.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.memory import SQLiteMemoryStore

_CHILD = r"""
import pathlib
import sys
import time

from ark.memory import (
    MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore,
)

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
owner, namespace, source = sys.argv[4:7]
store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("memory creation fixture gate timed out")
    time.sleep(0.02)
try:
    record = store.put(
        MemoryWrite(
            MemoryScope(owner, namespace), source,
            "private-test-content-" + ready.name,
        ),
        expected_revision=0,
    )
except MemoryConflictError:
    print("CONFLICT", flush=True)
else:
    assert record.revision == 1
    assert record.scope.owner_id == owner
    assert record.scope.namespace == namespace
    print("CREATED", flush=True)
"""


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("same-identity", ("CONFLICT", "CREATED")),
        ("separate-owner", ("CREATED", "CREATED")),
        ("separate-namespace", ("CREATED", "CREATED")),
        ("separate-source", ("CREATED", "CREATED")),
    ],
)
def test_concurrent_memory_initial_create_is_single_cas_per_identity(
    tmp_path, mode, expected,
):
    path = tmp_path / "memory.sqlite3"
    SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    # Keep one real WAL read epoch across BOTH child exits. A store instance
    # is not a live connection: short-lived connections can make another
    # process observe SQLite's transient last-close -shm unlink. This test
    # isolates revision-zero CAS. Unkept WAL lifecycle refusals are tested
    # separately without weakening any production sidecar checks.
    keeper = sqlite3.connect(path)
    assert keeper.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    keeper.execute("BEGIN")
    keeper.execute("SELECT COUNT(*) FROM memories").fetchone()
    gate = tmp_path / "start"
    first = ("fixture-owner", "private", "source")
    second = {
        "same-identity": first,
        "separate-owner": ("second-owner", "private", "source"),
        "separate-namespace": ("fixture-owner", "other", "source"),
        "separate-source": ("fixture-owner", "private", "other-source"),
    }[mode]
    identities = (first, second)
    # Test independent process CAS after both store handles are ready. The
    # constructor's WAL/schema bootstrap is independently covered elsewhere;
    # racing it here mixes startup contention into the revision-zero CAS test.
    # Start each worker and await its readiness before launching the next one.
    workers = []
    answers = []
    try:
        for index in range(2):
            worker = subprocess.Popen(
                [
                    sys.executable, "-c", _CHILD, str(path), str(gate),
                    str(tmp_path / f"ready-{index}"), *identities[index],
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            workers.append(worker)
            deadline = time.monotonic() + 25
            while not (tmp_path / f"ready-{index}").exists():
                if worker.poll() is not None:
                    _, error = worker.communicate()
                    raise AssertionError(
                        f"Memory worker {index} exited during bootstrap: {error[-3000:]}"
                    )
                if time.monotonic() >= deadline:
                    raise AssertionError(f"Memory worker {index} did not reach release")
                time.sleep(0.02)
        # Only the CAS put is concurrent. Both child handles remain live
        # behind the shared release gate until all workers are ready.
        gate.touch()
        answers = [worker.communicate(timeout=35) for worker in workers]
    finally:
        gate.touch()
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.communicate()
        keeper.close()
    assert all(worker.returncode == 0 for worker in workers), answers
    assert tuple(sorted(out.strip() for out, _ in answers)) == expected
    created = expected.count("CREATED")
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """SELECT memory_id, owner_id, namespace, source_id, revision,
                      content_sha256 FROM memories ORDER BY memory_id"""
        ).fetchall()
        events = conn.execute(
            """SELECT owner_id, namespace, operation, revision
               FROM memory_events ORDER BY event_id"""
        ).fetchall()
    assert len(rows) == len(events) == created
    assert len({row[0] for row in rows}) == created
    assert all(row[4] == 1 and len(row[5]) == 64 for row in rows)
    assert all(row[2:] == ("create", 1) for row in events)
    assert sorted((row[1], row[2]) for row in rows) == sorted(
        (row[0], row[1]) for row in events
    )
