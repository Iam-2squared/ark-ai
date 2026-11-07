"""Cross-process global expiry purge races a scoped Memory CAS refresh.

Only temporary local SQLite records and source-neutral audit events are used.
The purge must not erase a refresh that committed first in another process.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

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
mode = sys.argv[4]
store = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("global purge gate timed out")
    time.sleep(0.02)
if mode == "purge":
    print("PURGED:" + str(store.purge_expired()), flush=True)
else:
    try:
        result = store.put(
            MemoryWrite(
                MemoryScope("offline-owner", "namespace-a"),
                "alpha", "refreshed", expires_at_ms=5000,
            ),
            expected_revision=1,
        )
    except MemoryConflictError:
        print("CONFLICT", flush=True)
    else:
        assert result.revision == 2
        print("UPDATED", flush=True)
"""


@pytest.mark.parametrize("iteration", range(2))
def test_global_expiry_purge_and_refresh_preserve_all_scope_events(
    tmp_path, iteration,
):
    path = tmp_path / f"global-{iteration}.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    for namespace, source in (
        ("namespace-a", "alpha"), ("namespace-b", "beta"),
    ):
        store.put(
            MemoryWrite(
                MemoryScope("offline-owner", namespace), source, "fixture",
                expires_at_ms=1500,
            ),
        )
    gate = tmp_path / f"start-{iteration}"
    workers = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(tmp_path / f"ready-{iteration}-{index}"), action,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index, action in enumerate(("purge", "refresh"))
    ]
    try:
        deadline = time.monotonic() + 25
        while not all(
            (tmp_path / f"ready-{iteration}-{index}").exists()
            for index in range(2)
        ):
            if any(worker.poll() is not None for worker in workers):
                raise AssertionError("Memory purge worker exited before release")
            if time.monotonic() >= deadline:
                raise AssertionError("Memory purge workers did not reach release")
            time.sleep(0.02)
        gate.touch()
        replies = [worker.communicate(timeout=35) for worker in workers]
    finally:
        gate.touch()
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.communicate()
    assert all(worker.returncode == 0 for worker in workers), replies
    purge_output, update_output = (stdout.strip() for stdout, _ in replies)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """SELECT namespace, source_id, revision, expires_at_ms
               FROM memories ORDER BY namespace"""
        ).fetchall()
        events = conn.execute(
            """SELECT namespace, operation, revision
               FROM memory_events ORDER BY event_id"""
        ).fetchall()
    assert events[:2] == [
        ("namespace-a", "create", 1),
        ("namespace-b", "create", 1),
    ]
    if purge_output == "PURGED:2":
        assert update_output == "CONFLICT"
        assert rows == []
        assert sorted(events[2:]) == [
            ("namespace-a", "expire", 1),
            ("namespace-b", "expire", 1),
        ]
    else:
        assert purge_output == "PURGED:1"
        assert update_output == "UPDATED"
        assert rows == [("namespace-a", "alpha", 2, 5000)]
        assert sorted(events[2:]) == [
            ("namespace-a", "update", 2),
            ("namespace-b", "expire", 1),
        ]
