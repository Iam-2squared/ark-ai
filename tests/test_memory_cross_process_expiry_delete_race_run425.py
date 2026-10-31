"""Real local-process Memory CAS races must emit one atomic audited effect.

All SQLite files and gates live in pytest temporary directories. No remote
services, credentials, sensor access, dispatch, or real-world authorization.
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

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
mode = sys.argv[4]
memory_id = sys.argv[5]
store = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
scope = MemoryScope("disconnected-owner", "private")
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("start gate timed out")
    time.sleep(0.02)
try:
    if mode == "purge":
        print("PURGED:" + str(store.purge_expired(scope=scope)), flush=True)
    elif mode == "delete":
        assert store.delete(memory_id, scope, expected_revision=1) is True
        print("DELETED", flush=True)
    elif mode == "refresh":
        updated = store.put(
            MemoryWrite(
                scope, "source", "refreshed", expires_at_ms=5000,
            ),
            expected_revision=1,
        )
        assert updated.revision == 2
        print("UPDATED", flush=True)
    else:
        sys.exit("unknown child mode")
except MemoryConflictError:
    print("CONFLICT", flush=True)
"""


@pytest.mark.parametrize("iteration", range(2))
@pytest.mark.parametrize("mode", ("purge", "delete"))
def test_cross_process_expiry_or_delete_race_has_single_durable_effect(
    tmp_path, iteration, mode,
):
    root = tmp_path / f"{mode}-{iteration}"
    root.mkdir()
    path = root / "memory.sqlite3"
    scope = MemoryScope("disconnected-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    original = store.put(
        MemoryWrite(scope, "source", "initial", expires_at_ms=1500),
    )
    gate = root / "start"
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(root / f"ready-{index}"), action, original.memory_id,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index, action in enumerate((mode, "refresh"))
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((root / f"ready-{index}").exists() for index in range(2)):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("a competing process exited before the CAS gate")
            if time.monotonic() >= deadline:
                raise AssertionError("competing processes never reached the CAS gate")
            time.sleep(0.02)
        gate.touch()
        replies = [process.communicate(timeout=35) for process in processes]
    finally:
        gate.touch()
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert all(process.returncode == 0 for process in processes), replies
    output = tuple(stdout.strip() for stdout, _stderr in replies)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT revision, content, expires_at_ms FROM memories",
        ).fetchall()
        events = conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id",
        ).fetchall()

    if mode == "purge":
        if output == ("PURGED:1", "CONFLICT"):
            assert rows == []
            assert events == [("create", 1), ("expire", 1)]
        else:
            assert output == ("PURGED:0", "UPDATED")
            assert rows == [(2, "refreshed", 5000)]
            assert events == [("create", 1), ("update", 2)]
    elif output == ("DELETED", "CONFLICT"):
        assert rows == []
        assert events == [("create", 1), ("delete", 1)]
    else:
        assert output == ("CONFLICT", "UPDATED")
        assert rows == [(2, "refreshed", 5000)]
        assert events == [("create", 1), ("update", 2)]
